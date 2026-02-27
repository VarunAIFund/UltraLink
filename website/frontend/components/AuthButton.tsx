"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogIn } from "lucide-react";
import { useAuth } from "@/lib/useAuth";

/**
 * Shows a "Sign In" button when the user is not authenticated.
 * Renders nothing when authenticated (sign-out lives in the Sidebar).
 */
export default function AuthButton() {
  const { isAuthenticated, loading } = useAuth();
  const pathname = usePathname();

  if (loading || isAuthenticated) return null;

  return (
    <Link
      href={`/login?redirect=${encodeURIComponent(pathname)}`}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-primary hover:bg-primary/90 text-primary-foreground transition-colors"
    >
      <LogIn className="h-4 w-4" />
      Sign In
    </Link>
  );
}
