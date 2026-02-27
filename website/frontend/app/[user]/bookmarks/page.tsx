"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { getUserBookmarks, getUser, type Bookmark } from "@/lib/api";
import { createBrowserClient } from "@/lib/supabase";
import HamburgerMenu from "@/components/HamburgerMenu";
import Sidebar from "@/components/Sidebar";
import { BookmarkedCandidateCard } from "@/components/BookmarkedCandidateCard";
import { motion } from "framer-motion";
import { Star } from "lucide-react";
import { useAuth } from "@/lib/useAuth";

export default function BookmarksPage() {
  const params = useParams();
  const router = useRouter();
  const userName = params?.user as string;
  const { session, loading: authLoading } = useAuth();

  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Two independent pieces of state that resolve in parallel:
  // null = still loading; string = resolved
  const [urlUserDisplayName, setUrlUserDisplayName] = useState<string | null>(null);
  const [ownerConfirmed, setOwnerConfirmed] = useState(false);

  // Effect 1: Validate the URL user exists — runs immediately, no auth dependency
  useEffect(() => {
    if (!userName) return;
    getUser(userName)
      .then((data) => {
        if (data.success) setUrlUserDisplayName(data.user.display_name);
        else router.replace("/");
      })
      .catch(() => router.replace("/"));
  }, [userName, router]);

  // Effect 2: Ownership check — fires once BOTH user validation AND auth are done
  useEffect(() => {
    if (authLoading || urlUserDisplayName === null) return;

    if (!session?.user?.email) {
      router.replace(`/login?redirect=/${userName}/bookmarks`);
      return;
    }

    const supabase = createBrowserClient();
    supabase
      .from("users")
      .select("username")
      .ilike("email", session.user.email!)
      .single()
      .then(({ data }) => {
        if (data?.username === userName) {
          setOwnerConfirmed(true);
        } else {
          router.replace(data?.username ? `/${data.username}/` : "/");
        }
      });
  }, [authLoading, urlUserDisplayName, session, userName, router]);

  // Effect 3: Load bookmarks once ownership is confirmed
  useEffect(() => {
    if (!ownerConfirmed || !userName) return;
    setLoading(true);
    getUserBookmarks(userName)
      .then((data) => {
        if (data.success) setBookmarks(data.bookmarks);
        else setError(data.error || "Failed to load bookmarks");
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load bookmarks");
      })
      .finally(() => setLoading(false));
  }, [ownerConfirmed, userName]);

  const handleRemoveBookmark = (bookmarkId: string) => {
    setBookmarks((prev) => prev.filter((b) => b.id !== bookmarkId));
  };

  // Show spinner until ownership is confirmed
  if (!ownerConfirmed) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-foreground" />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <HamburgerMenu onOpen={() => setSidebarOpen(true)} />
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        userName={userName}
      />

      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8 mt-12"
      >
        <h1 className="text-4xl font-bold mb-2">
          {urlUserDisplayName ? `${urlUserDisplayName}'s Bookmarks` : "Bookmarks"}
        </h1>
        <p className="text-muted-foreground">
          Your saved candidates for easy access
        </p>
      </motion.div>

      {error && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-6"
        >
          {error}
        </motion.div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-64 bg-muted rounded-xl"></div>
            </div>
          ))}
        </div>
      ) : bookmarks.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <Star className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
          <h2 className="text-2xl font-semibold mb-2">No Bookmarks Yet</h2>
          <p className="text-muted-foreground mb-6">
            Start bookmarking candidates to save them for later
          </p>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h2 className="text-2xl font-semibold mb-6">
            {bookmarks.length} Bookmarked Candidate
            {bookmarks.length !== 1 ? "s" : ""}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {bookmarks.map((bookmark, index) => (
              <motion.div
                key={bookmark.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <BookmarkedCandidateCard
                  bookmark={bookmark}
                  userName={userName}
                  onRemove={handleRemoveBookmark}
                />
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
