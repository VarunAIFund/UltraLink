import { createBrowserClient as _createBrowserClient, createServerClient as _createServerClient } from "@supabase/ssr";
import type { ReadonlyRequestCookies } from "next/dist/server/web/spec-extension/adapters/request-cookies";
import type { NextRequest, NextResponse } from "next/server";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

/** Use in 'use client' components */
export function createBrowserClient() {
  return _createBrowserClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}

/** Use in Server Components and Route Handlers (reads cookies from a ReadonlyRequestCookies store) */
export function createServerClient(cookieStore: ReadonlyRequestCookies) {
  return _createServerClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll() {
        // ReadonlyRequestCookies cannot set cookies — mutations happen in middleware
      },
    },
  });
}

/**
 * Look up a platform user by email, checking both primary email and secondary_emails.
 * Returns {username, display_name, role} or null if not found.
 *
 * Use this everywhere you need to map session.user.email → platform username
 * so that secondary-email logins work correctly.
 */
export async function getUserBySessionEmail(
  email: string
): Promise<{ username: string; display_name: string; role: string } | null> {
  const supabase = createBrowserClient();

  // 1. Try primary email
  const { data: primary } = await supabase
    .from("users")
    .select("username, display_name, role")
    .ilike("email", email)
    .maybeSingle();
  if (primary) return primary;

  // 2. Try secondary emails (.contains() quotes values properly for array literals)
  const { data: secondary } = await supabase
    .from("users")
    .select("username, display_name, role")
    .contains("secondary_emails", [email.toLowerCase()])
    .maybeSingle();
  return secondary ?? null;
}

/** Use in middleware (needs access to both req and res to refresh sessions) */
export function createMiddlewareClient(request: NextRequest, response: NextResponse) {
  return _createServerClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
        cookiesToSet.forEach(({ name, value, options }) =>
          response.cookies.set(name, value, options)
        );
      },
    },
  });
}
