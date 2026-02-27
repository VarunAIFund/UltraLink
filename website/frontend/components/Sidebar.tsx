"use client";

import { X, Search, Star, LogOut } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "./ui/button";
import { getUser } from "@/lib/api";
import { createBrowserClient } from "@/lib/supabase";
import { useAuth } from "@/lib/useAuth";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  userName: string;
}

export default function Sidebar({ isOpen, onClose, userName }: SidebarProps) {
  const router = useRouter();
  const { isAuthenticated, session, loading: authLoading } = useAuth();
  // The username/display name of the *signed-in* user (may differ from URL userName)
  const [activeUserName, setActiveUserName] = useState(userName);
  const [userDisplayName, setUserDisplayName] = useState("");
  const [signingOut, setSigningOut] = useState(false);

  const handleSignOut = async () => {
    setSigningOut(true);
    const supabase = createBrowserClient();
    await supabase.auth.signOut();
    router.push("/login");
  };

  // When authenticated, look up the signed-in user's info from their session email.
  // This ensures the sidebar always shows the logged-in user, not the URL user.
  // Wait for authLoading to finish before acting to avoid the unauthenticated
  // fallback firing while the session is still being resolved.
  useEffect(() => {
    if (authLoading) return;

    if (isAuthenticated && session?.user?.email) {
      (async () => {
        try {
          const supabase = createBrowserClient();
          const { data } = await supabase
            .from("users")
            .select("username, display_name")
            .ilike("email", session.user.email!)
            .single();
          if (data) {
            setActiveUserName(data.username);
            setUserDisplayName(data.display_name);
          }
        } catch (err) {
          console.error("Error fetching signed-in user info:", err);
        }
      })();
    } else if (!isAuthenticated && userName) {
      // Unauthenticated: fall back to URL user display name
      getUser(userName)
        .then((data) => {
          if (data.success) setUserDisplayName(data.user.display_name);
        })
        .catch((err) => console.error("Error fetching user info:", err));
    }
  }, [authLoading, isAuthenticated, session, userName]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40"
          />

          {/* Sidebar */}
          <motion.div
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed top-0 left-0 h-full w-80 bg-sidebar text-sidebar-foreground shadow-xl z-50 p-6 border-r border-sidebar-border"
          >
            {/* Close button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="absolute top-4 right-4 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              aria-label="Close menu"
            >
              <X className="h-6 w-6" />
            </Button>

            {/* User display name */}
            <div className="mt-2 mb-8">
              <h2 className="text-2xl font-bold text-sidebar-foreground">
                {userDisplayName || activeUserName}
              </h2>
            </div>

            {/* Navigation links — only show when authenticated */}
            {isAuthenticated ? (
              <nav className="space-y-4">
                <Link
                  href={`/${activeUserName}/searches`}
                  onClick={onClose}
                  className="flex items-center gap-3 p-3 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
                >
                  <Search className="h-5 w-5" />
                  <span className="text-lg">Past Searches</span>
                </Link>

                <Link
                  href={`/${activeUserName}/bookmarks`}
                  onClick={onClose}
                  className="flex items-center gap-3 p-3 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
                >
                  <Star className="h-5 w-5" />
                  <span className="text-lg">Bookmarks</span>
                </Link>
              </nav>
            ) : (
              <p className="text-sm text-muted-foreground">
                Sign in to access your searches and bookmarks.
              </p>
            )}

            {/* Bottom actions */}
            <div className="absolute bottom-6 left-6 right-6 space-y-2">
              <Link
                href={`/${activeUserName}`}
                onClick={onClose}
                className="block w-full p-3 text-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground hover:bg-sidebar-primary/90 transition-colors"
              >
                Back to Search
              </Link>
              {isAuthenticated ? (
                <button
                  type="button"
                  onClick={handleSignOut}
                  disabled={signingOut}
                  className="flex items-center justify-center gap-2 w-full p-3 rounded-lg text-sm text-muted-foreground hover:bg-sidebar-accent hover:text-red-500 transition-colors disabled:opacity-50"
                >
                  <LogOut className="h-4 w-4" />
                  {signingOut ? "Signing out..." : "Sign out"}
                </button>
              ) : (
                <Link
                  href={`/login?redirect=/${userName}`}
                  onClick={onClose}
                  className="flex items-center justify-center gap-2 w-full p-3 rounded-lg text-sm text-primary hover:bg-primary/5 dark:hover:bg-primary/10 transition-colors"
                >
                  <LogOut className="h-4 w-4 rotate-180" />
                  Sign in
                </Link>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
