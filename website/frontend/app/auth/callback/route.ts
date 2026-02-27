import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const redirect = searchParams.get("redirect");

  if (!code) {
    return NextResponse.redirect(`${origin}/login?error=missing_code`);
  }

  // We need a mutable response so we can write session cookies onto it
  const response = NextResponse.redirect(`${origin}/login?error=auth_failed`);

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => {
            response.cookies.set(name, value, options);
          });
        },
      },
    }
  );

  const { data, error } = await supabase.auth.exchangeCodeForSession(code);

  if (error || !data.session) {
    console.error("Auth callback error:", error?.message);
    return response; // redirects to /login?error=auth_failed
  }

  const authEmail = data.session.user.email?.toLowerCase();

  if (!authEmail) {
    await supabase.auth.signOut();
    return NextResponse.redirect(`${origin}/login?error=no_email`);
  }

  // Look up username from public users table by email
  const { data: userData, error: userError } = await supabase
    .from("users")
    .select("username")
    .ilike("email", authEmail)
    .single();

  if (userError || !userData) {
    await supabase.auth.signOut();
    return NextResponse.redirect(
      `${origin}/login?error=unauthorized&email=${encodeURIComponent(authEmail)}`
    );
  }

  const username = userData.username;

  // Validate the redirect param belongs to this user's workspace
  const destination =
    redirect && redirect.startsWith(`/${username}/`)
      ? `${origin}${redirect}`
      : `${origin}/${username}/`;

  // Update the redirect on the response (cookies are already set on it)
  response.headers.set("Location", destination);
  return response;
}
