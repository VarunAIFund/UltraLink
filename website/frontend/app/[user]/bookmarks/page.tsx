"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { getUserBookmarks, getUser, type Bookmark } from "@/lib/api";
import HamburgerMenu from "@/components/HamburgerMenu";
import Sidebar from "@/components/Sidebar";
import { CandidateCard } from "@/components/CandidateCard";
import { motion } from "framer-motion";
import { Star } from "lucide-react";

export default function BookmarksPage() {
  const params = useParams();
  const userName = params?.user as string;

  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userDisplayName, setUserDisplayName] = useState<string>("");

  // Fetch user display name
  useEffect(() => {
    if (userName) {
      getUser(userName)
        .then((data) => {
          if (data.success) {
            setUserDisplayName(data.user.display_name);
          }
        })
        .catch((err) => {
          console.error('Error fetching user info:', err);
        });
    }
  }, [userName]);

  // Fetch bookmarks
  const loadBookmarks = () => {
    if (userName) {
      setLoading(true);
      getUserBookmarks(userName)
        .then((data) => {
          if (data.success) {
            setBookmarks(data.bookmarks);
          } else {
            setError(data.error || "Failed to load bookmarks");
          }
        })
        .catch((err) => {
          setError(err instanceof Error ? err.message : "Failed to load bookmarks");
        })
        .finally(() => {
          setLoading(false);
        });
    }
  };

  useEffect(() => {
    loadBookmarks();
  }, [userName]);

  return (
    <div className="min-h-screen p-8 max-w-5xl mx-auto">
      {/* Hamburger Menu */}
      <HamburgerMenu onOpen={() => setSidebarOpen(true)} />

      {/* Sidebar */}
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
          {userDisplayName ? `${userDisplayName}'s Bookmarks` : 'Bookmarks'}
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
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-48 bg-muted rounded-lg"></div>
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
          <h2 className="text-2xl font-semibold mb-4">
            {bookmarks.length} Bookmarked Candidate{bookmarks.length !== 1 ? 's' : ''}
          </h2>
          <div className="space-y-4">
            {bookmarks.map((bookmark, index) => (
              <motion.div
                key={bookmark.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <CandidateCard
                  candidate={{
                    ...bookmark.candidate,
                    linkedin_url: bookmark.linkedin_url,
                    relevance_score: 0,
                    fit_description: bookmark.notes || '',
                    match: 'strong' as const
                  }}
                  userName={userName}
                />
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
