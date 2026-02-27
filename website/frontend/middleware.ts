import { NextResponse, type NextRequest } from "next/server";
import { createMiddlewareClient } from "@/lib/supabase";

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip static assets and auth routes entirely
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/login") ||
    pathname.startsWith("/auth/callback") ||
    pathname === "/favicon.ico"
  ) {
    return NextResponse.next();
  }

  // If Supabase redirected a magic link code here (admin-sent links use Site URL),
  // forward it to our callback handler so the session can be established.
  const code = request.nextUrl.searchParams.get("code");
  if (code) {
    const callbackUrl = new URL("/auth/callback", request.url);
    callbackUrl.searchParams.set("code", code);
    return NextResponse.redirect(callbackUrl);
  }

  const response = NextResponse.next({
    request: { headers: request.headers },
  });

  const supabase = createMiddlewareClient(request, response);

  // Refresh session cookies on every request (keeps session alive)
  const {
    data: { session },
  } = await supabase.auth.getSession();

  // Admin routes require auth — hard protect
  const adminMatch = pathname.match(/^\/([^/]+)\/admin/);
  if (adminMatch && !session) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
