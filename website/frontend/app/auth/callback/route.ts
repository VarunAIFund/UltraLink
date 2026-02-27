import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get("code");
  const redirect = searchParams.get("redirect");

  // Behind a reverse proxy (Railway, Vercel, etc.) request.url contains the
  // internal container URL (e.g. http://localhost:3000).  Use the forwarded
  // headers to reconstruct the public-facing origin instead.
  const forwardedHost = request.headers.get("x-forwarded-host");
  const forwardedProto = request.headers.get("x-forwarded-proto") ?? "https";
  const origin = forwardedHost
    ? `${forwardedProto}://${forwardedHost}`
    : new URL(request.url).origin;

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

  // Look up username from public users table by primary OR secondary email.
  // We do two separate queries because the .or() raw filter with cs.{email}
  // doesn't quote email addresses properly in the array literal, causing
  // PostgREST to fail to match addresses containing @ or dots.

  // 1. Primary email (case-insensitive)
  const { data: primaryMatch } = await supabase
    .from("users")
    .select("username, email, secondary_emails")
    .ilike("email", authEmail)
    .maybeSingle();

  // 2. Secondary email — .contains() quotes values correctly
  let userData = primaryMatch;
  if (!userData) {
    const { data: secondaryMatch } = await supabase
      .from("users")
      .select("username, email, secondary_emails")
      .contains("secondary_emails", [authEmail])
      .maybeSingle();
    userData = secondaryMatch;
  }

  if (!userData) {
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
