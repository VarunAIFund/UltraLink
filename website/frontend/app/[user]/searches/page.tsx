"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { getUserSearches, getUser, type SearchHistoryItem } from "@/lib/api";
import HamburgerMenu from "@/components/HamburgerMenu";
import Sidebar from "@/components/Sidebar";
import { motion } from "framer-motion";
import { Search, Clock } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function SearchHistoryPage() {
  const params = useParams();
  const router = useRouter();
  const userName = params?.user as string;

  const [searches, setSearches] = useState<SearchHistoryItem[]>([]);
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

  // Fetch search history
  useEffect(() => {
    if (userName) {
      getUserSearches(userName)
        .then((data) => {
          if (data.success) {
            setSearches(data.searches);
          } else {
            setError(data.error || "Failed to load searches");
          }
        })
        .catch((err) => {
          setError(err instanceof Error ? err.message : "Failed to load searches");
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [userName]);

  const handleSearchClick = (searchId: string) => {
    router.push(`/${userName}/search/${searchId}`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

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
          {userDisplayName ? `${userDisplayName}'s Search History` : 'Search History'}
        </h1>
        <p className="text-muted-foreground">
          View and revisit your previous searches
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
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-6 bg-muted rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-muted rounded w-1/2"></div>
              </CardHeader>
            </Card>
          ))}
        </div>
      ) : searches.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <Search className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
          <h2 className="text-2xl font-semibold mb-2">No Searches Yet</h2>
          <p className="text-muted-foreground mb-6">
            Start searching to build your search history
          </p>
          <button
            onClick={() => router.push(`/${userName}`)}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Start Searching
          </button>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="space-y-4"
        >
          {searches.map((search, index) => (
            <motion.div
              key={search.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <Card
                className="cursor-pointer hover:shadow-lg transition-shadow"
                onClick={() => handleSearchClick(search.id)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <CardTitle className="text-lg mb-2">
                        {search.query}
                      </CardTitle>
                      <CardDescription className="flex items-center gap-4 text-sm">
                        <span className="flex items-center gap-1">
                          <Search className="w-4 h-4" />
                          {search.total_results} results
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {formatDate(search.created_at)}
                        </span>
                        {search.status && (
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            search.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                            search.status === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                            'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                          }`}>
                            {search.status}
                          </span>
                        )}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
