"use client";

import { X, Search, Star } from "lucide-react";
import { Shield } from "lucide-react"; // Admin icon - uncomment when re-enabling admin
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import Link from "next/link";
import { Button } from "./ui/button";
import { getUser, checkIsAdmin } from "@/lib/api";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  userName: string;
}

export default function Sidebar({ isOpen, onClose, userName }: SidebarProps) {
  const [userDisplayName, setUserDisplayName] = useState(userName);
  const [isAdmin, setIsAdmin] = useState(false);

  // Fetch user info to get display name
  useEffect(() => {
    if (userName) {
      getUser(userName)
        .then((data) => {
          if (data.success) {
            setUserDisplayName(data.user.display_name);
          }
        })
        .catch((err) => {
          console.error("Error fetching user info:", err);
        });

      // Check if user is admin - commented out for now
      /*
      checkIsAdmin(userName)
        .then((data) => {
          if (data.success) {
            setIsAdmin(data.is_admin);
          }
        })
        .catch((err) => {
          console.error("Error checking admin status:", err);
        });
      */
    }
  }, [userName]);

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
                {userDisplayName}
              </h2>
            </div>

            {/* Navigation links */}
            <nav className="space-y-4">
              <Link
                href={`/${userName}/searches`}
                onClick={onClose}
                className="flex items-center gap-3 p-3 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
              >
                <Search className="h-5 w-5" />
                <span className="text-lg">Past Searches</span>
              </Link>

              <Link
                href={`/${userName}/bookmarks`}
                onClick={onClose}
                className="flex items-center gap-3 p-3 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
              >
                <Star className="h-5 w-5" />
                <span className="text-lg">Bookmarks</span>
              </Link>

              {/* Admin link - commented out for now
              {isAdmin && (
                <Link
                  href={`/${userName}/admin`}
                  onClick={onClose}
                  className="flex items-center gap-3 p-3 rounded-lg text-amber-500 hover:bg-amber-500/10 hover:text-amber-400 transition-colors border border-amber-500/30"
                >
                  <Shield className="h-5 w-5" />
                  <span className="text-lg font-medium">Admin</span>
                </Link>
              )}
              */}
            </nav>

            {/* Back to search */}
            <div className="absolute bottom-6 left-6 right-6">
              <Link
                href={`/${userName}`}
                onClick={onClose}
                className="block w-full p-3 text-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground hover:bg-sidebar-primary/90 transition-colors"
              >
                Back to Search
              </Link>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
