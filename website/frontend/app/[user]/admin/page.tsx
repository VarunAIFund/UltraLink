"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getAdminSearches,
  checkIsAdmin,
  getAllUsers,
  type AdminSearchItem,
  type User,
} from "@/lib/api";
import HamburgerMenu from "@/components/HamburgerMenu";
import Sidebar from "@/components/Sidebar";
import { motion, AnimatePresence } from "framer-motion";
import { Shield, Search, Clock, User as UserIcon, ChevronDown, ChevronRight } from "lucide-react";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface UserWithSearches extends User {
  searches: AdminSearchItem[];
  searchCount: number;
}

export default function AdminPage() {
  const params = useParams();
  const router = useRouter();
  const userName = params?.user as string;

  const [usersWithSearches, setUsersWithSearches] = useState<UserWithSearches[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [expandedUser, setExpandedUser] = useState<string | null>(null);

  // Check if user is admin
  useEffect(() => {
    if (userName) {
      checkIsAdmin(userName)
        .then((data) => {
          if (data.success && data.is_admin) {
            setIsAdmin(true);
          } else {
            // Redirect non-admin users
            router.push(`/${userName}`);
          }
        })
        .catch((err) => {
          console.error("Error checking admin status:", err);
          router.push(`/${userName}`);
        })
        .finally(() => {
          setAuthChecked(true);
        });
    }
  }, [userName, router]);

  // Fetch all users and searches (admin only)
  useEffect(() => {
    if (userName && isAdmin) {
      Promise.all([getAllUsers(), getAdminSearches(userName)])
        .then(([usersData, searchesData]) => {
          if (usersData.success && searchesData.success) {
            // Group searches by user
            const searchesByUser: Record<string, AdminSearchItem[]> = {};
            for (const search of searchesData.searches) {
              const userKey = search.user_name || "unknown";
              if (!searchesByUser[userKey]) {
                searchesByUser[userKey] = [];
              }
              searchesByUser[userKey].push(search);
            }

            // Combine users with their searches
            const combined: UserWithSearches[] = usersData.users.map((user) => ({
              ...user,
              searches: searchesByUser[user.username] || [],
              searchCount: (searchesByUser[user.username] || []).length,
            }));

            // Sort by search count (most active users first)
            combined.sort((a, b) => b.searchCount - a.searchCount);

            setUsersWithSearches(combined);
          } else {
            setError("Failed to load data");
          }
        })
        .catch((err) => {
          setError(err instanceof Error ? err.message : "Failed to load data");
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [userName, isAdmin]);

  const handleUserClick = (userUsername: string) => {
    setExpandedUser(expandedUser === userUsername ? null : userUsername);
  };

  const handleSearchClick = (search: AdminSearchItem) => {
    // Navigate to the search using the search owner's username
    router.push(`/${search.user_name}/search/${search.id}`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Show nothing while checking auth
  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  // Non-admin users should have been redirected
  if (!isAdmin) {
    return null;
  }

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
        <div className="flex items-center gap-3 mb-2">
          <Shield className="h-8 w-8 text-amber-500" />
          <h1 className="text-4xl font-bold">Admin Dashboard</h1>
        </div>
        <p className="text-muted-foreground">
          Click on a user to view their search history
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
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-6 bg-muted rounded w-1/3 mb-2"></div>
                <div className="h-4 bg-muted rounded w-1/4"></div>
              </CardHeader>
            </Card>
          ))}
        </div>
      ) : usersWithSearches.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <UserIcon className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
          <h2 className="text-2xl font-semibold mb-2">No Users Found</h2>
          <p className="text-muted-foreground">No users have been registered yet</p>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="space-y-4"
        >
          {usersWithSearches.map((user, index) => (
            <motion.div
              key={user.username}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              {/* User Card */}
              <Card
                className={`cursor-pointer transition-all border-l-4 ${
                  expandedUser === user.username
                    ? "border-l-amber-500 shadow-lg"
                    : "border-l-transparent hover:border-l-amber-500/50 hover:shadow-md"
                }`}
                onClick={() => handleUserClick(user.username)}
              >
                <CardHeader className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                        <UserIcon className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{user.display_name}</CardTitle>
                        <CardDescription className="text-sm">
                          @{user.username} • {user.email}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-muted-foreground">
                        {user.searchCount} {user.searchCount === 1 ? "search" : "searches"}
                      </span>
                      {expandedUser === user.username ? (
                        <ChevronDown className="w-5 h-5 text-amber-500" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-muted-foreground" />
                      )}
                    </div>
                  </div>
                </CardHeader>
              </Card>

              {/* Expanded Searches */}
              <AnimatePresence>
                {expandedUser === user.username && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="ml-6 mt-2 border-l-2 border-amber-500/30 pl-4">
                      {user.searches.length === 0 ? (
                        <div className="py-4 text-muted-foreground text-sm">
                          No searches yet
                        </div>
                      ) : (
                        <div className="max-h-80 overflow-y-auto space-y-2 pr-2">
                          {user.searches.map((search) => (
                            <motion.div
                              key={search.id}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              className="cursor-pointer"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSearchClick(search);
                              }}
                            >
                              <Card className="hover:shadow-md transition-shadow bg-muted/30">
                                <CardHeader className="py-3 px-4">
                                  <CardTitle className="text-base font-medium">
                                    {search.query}
                                  </CardTitle>
                                  <CardDescription className="flex items-center gap-3 text-xs">
                                    <span className="flex items-center gap-1">
                                      <Search className="w-3 h-3" />
                                      {search.total_results} results
                                    </span>
                                    <span className="flex items-center gap-1">
                                      <Clock className="w-3 h-3" />
                                      {formatDate(search.created_at)}
                                    </span>
                                    {search.status && (
                                      <span
                                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                          search.status === "completed"
                                            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                                            : search.status === "failed"
                                            ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                                            : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                                        }`}
                                      >
                                        {search.status}
                                      </span>
                                    )}
                                  </CardDescription>
                                </CardHeader>
                              </Card>
                            </motion.div>
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}

