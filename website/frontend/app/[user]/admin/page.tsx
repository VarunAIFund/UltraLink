"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getAdminSearches,
  checkIsAdmin,
  getAllUsers,
  uploadCSV,
  getUploadJobs,
  getAllReceivers,
  type AdminSearchItem,
  type User,
  type UploadJob,
  type Receiver,
} from "@/lib/api";
import HamburgerMenu from "@/components/HamburgerMenu";
import Sidebar from "@/components/Sidebar";
import { motion, AnimatePresence } from "framer-motion";
import { Shield, Search, Clock, User as UserIcon, ChevronDown, ChevronRight, Upload, FileUp, Loader2 } from "lucide-react";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

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
  
  // CSV Upload states
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [jobs, setJobs] = useState<UploadJob[]>([]);
  const [expandedJob, setExpandedJob] = useState<string | null>(null);
  const [receivers, setReceivers] = useState<Receiver[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
      loadData();
    }
  }, [userName, isAdmin]);
  
  // Auto-refresh jobs every 10 seconds if any are processing
  useEffect(() => {
    if (!userName || !isAdmin) return;
    
    const hasProcessingJobs = jobs.some(j => 
      j.status === 'scraping' || j.status === 'transforming' || j.status === 'pending'
    );
    
    if (hasProcessingJobs) {
      const interval = setInterval(() => {
        loadJobs();
      }, 15000); // 15 seconds (reduced polling to avoid connection issues)
      
      return () => clearInterval(interval);
    }
  }, [userName, isAdmin, jobs]);
  
  const loadData = async () => {
    try {
      const [usersData, searchesData, jobsData, receiversData] = await Promise.all([
        getAllUsers(),
        getAdminSearches(userName),
        getUploadJobs(userName),
        getAllReceivers()
      ]);
      
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
      
      if (jobsData.success) {
        setJobs(jobsData.jobs);
      }
      
      if (receiversData.success) {
        setReceivers(receiversData.receivers);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };
  
  const loadJobs = async () => {
    try {
      const jobsData = await getUploadJobs(userName);
      if (jobsData.success) {
        setJobs(jobsData.jobs);
      }
    } catch (err) {
      console.error("Failed to refresh jobs:", err);
    }
  };

  const handleUserClick = (userUsername: string) => {
    setExpandedUser(expandedUser === userUsername ? null : userUsername);
  };

  const handleSearchClick = (search: AdminSearchItem) => {
    // Navigate to the search using the search owner's username
    router.push(`/${search.user_name}/search/${search.id}`);
  };
  
  const handleJobClick = (jobId: string) => {
    setExpandedJob(expandedJob === jobId ? null : jobId);
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
  
  // Check if any jobs are currently processing
  const hasProcessingJobs = jobs.some(
    (job) => job.status === 'scraping' || job.status === 'transforming'
  );
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.csv')) {
        setUploadError('Please select a CSV file');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setUploadError('');
      setUploadSuccess('');
    }
  };
  
  const handleUpload = async () => {
    if (!selectedFile) return;
    
    setUploading(true);
    setUploadError('');
    setUploadSuccess('');
    
    try {
      const result = await uploadCSV(selectedFile, userName);
      if (result.success) {
        setUploadSuccess('CSV uploaded and processed successfully!');
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        // Reload jobs
        await loadJobs();
      }
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
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
          Upload CSVs and manage user activity
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
      
      {/* CSV Upload Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="mb-8"
      >
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileUp className="h-5 w-5 text-amber-500" />
              <CardTitle>Upload LinkedIn Connections CSV</CardTitle>
            </div>
            <CardDescription>
              Upload a CSV file with LinkedIn profile URLs. The connection owner will be auto-detected from the filename.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Naming Instructions */}
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-2">
                <div className="flex items-center gap-2 text-amber-900 font-semibold">
                  <FileUp className="h-4 w-4" />
                  File Naming Convention
                </div>
                <p className="text-sm text-amber-800">
                  Name your CSV file as: <code className="bg-amber-100 px-2 py-1 rounded text-xs font-mono">name_connections.csv</code>
                </p>
                <p className="text-sm text-amber-700">
                  Examples: <code className="bg-amber-100 px-1.5 py-0.5 rounded text-xs font-mono">linda_connections.csv</code>, <code className="bg-amber-100 px-1.5 py-0.5 rounded text-xs font-mono">dan_connections.csv</code>, <code className="bg-amber-100 px-1.5 py-0.5 rounded text-xs font-mono">varun_connections.csv</code>
                </p>
                <p className="text-sm text-amber-700 mt-2">
                  💡 <strong>Tip:</strong> To update existing connections, simply upload a new CSV with the same name. New profiles will be added and existing ones will be updated.
                </p>
              </div>
              
              {/* Current Connection Owners */}
              {receivers.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2">
                  <div className="flex items-center gap-2 text-blue-900 font-semibold">
                    <UserIcon className="h-4 w-4" />
                    Current Connection Owners
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {receivers.map((receiver) => (
                      <span
                        key={receiver.username}
                        className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-medium"
                      >
                        {receiver.display_name} ({receiver.username})
                      </span>
                    ))}
                  </div>
                  <p className="text-sm text-blue-700 mt-2">
                    These names are already in the system. New names will be automatically added when you upload.
                  </p>
                </div>
              )}
              
              <div className="flex items-center gap-4">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  disabled={uploading || hasProcessingJobs}
                  className="file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-amber-50 file:text-amber-700 hover:file:bg-amber-100 disabled:opacity-50"
                />
                <Button
                  onClick={handleUpload}
                  disabled={!selectedFile || uploading || hasProcessingJobs}
                  className="bg-amber-500 hover:bg-amber-600"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      Upload & Process
                    </>
                  )}
                </Button>
              </div>
              
              {uploadError && (
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-2 rounded text-sm">
                  {uploadError}
                </div>
              )}
              
              {hasProcessingJobs && (
                <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-2 rounded text-sm flex items-center">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Upload disabled - A job is currently processing. Please wait for it to complete.
                </div>
              )}
              
              {uploadSuccess && (
                <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-2 rounded text-sm">
                  {uploadSuccess}
                </div>
              )}
              
              {uploading && (
                <p className="text-sm text-muted-foreground">
                  This may take 20-30 minutes for large files. The job will continue even if you close this page.
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
      
      {/* Upload Jobs Table */}
      {jobs.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mb-8"
        >
          <h2 className="text-2xl font-bold mb-4">Recent Upload Jobs</h2>
          <div className="space-y-2">
            {jobs.map((job) => (
              <Card
                key={job.id}
                className={`cursor-pointer transition-all border-l-4 ${
                  expandedJob === job.id
                    ? "border-l-amber-500 shadow-lg"
                    : "border-l-transparent hover:border-l-amber-500/50 hover:shadow-md"
                }`}
                onClick={() => handleJobClick(job.id)}
              >
                <CardHeader className="py-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base">{job.filename}</CardTitle>
                      <CardDescription className="flex items-center gap-3 text-xs mt-1">
                        <span>By {job.uploaded_by}</span>
                        {job.connection_owner && <span>Owner: {job.connection_owner}</span>}
                        <span>{formatDate(job.created_at)}</span>
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-3">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          job.status === "completed"
                            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                            : job.status === "failed"
                            ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                            : job.status === "scraping" || job.status === "transforming"
                            ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 flex items-center gap-1"
                            : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                        }`}
                      >
                        {(job.status === "scraping" || job.status === "transforming") && (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        )}
                        {job.status}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        {job.scraped_urls} new, {job.total_urls - job.scraped_urls} existed
                        {job.status === 'scraping' && job.current_step && (
                          <span className="ml-2 text-blue-600 dark:text-blue-400">
                            ({job.current_step})
                          </span>
                        )}
                      </span>
                      {expandedJob === job.id ? (
                        <ChevronDown className="w-5 h-5 text-amber-500" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-muted-foreground" />
                      )}
                    </div>
                  </div>
                </CardHeader>
                
                {/* Expanded Job Details */}
                <AnimatePresence>
                  {expandedJob === job.id && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden border-t"
                    >
                      <div className="p-4 bg-muted/30 space-y-3 text-sm">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="col-span-2 pb-2 border-b border-muted">
                            <span className="font-medium">Total URLs in CSV:</span> {job.total_urls}
                          </div>
                          <div>
                            <span className="font-medium">Scraped (new):</span> {job.scraped_urls}
                          </div>
                          <div>
                            <span className="font-medium">Already existed:</span> {job.total_urls - job.scraped_urls}
                          </div>
                          <div>
                            <span className="font-medium">Transformed:</span> {job.transformed_urls}/{job.total_urls}
                          </div>
                          <div>
                            <span className="font-medium">Failed:</span> {job.failed_urls}
                          </div>
                          {job.current_step && (
                            <div className="col-span-2 pt-2 border-t border-muted">
                              <span className="font-medium">Current Step:</span> {job.current_step}
                            </div>
                          )}
                        </div>
                        
                        {job.error_message && (
                          <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded mt-2">
                            <span className="font-medium">Error:</span> {job.error_message}
                          </div>
                        )}
                        
                        {job.logs && (
                          <details 
                            className="mt-2" 
                            onClick={(e) => e.stopPropagation()}
                          >
                            <summary className="cursor-pointer font-medium hover:text-amber-600">
                              View Logs
                            </summary>
                            <div className="mt-2 border border-muted rounded overflow-hidden">
                              <pre className="p-3 bg-black/5 dark:bg-white/5 text-xs overflow-auto max-h-96">
                                {job.logs}
                              </pre>
                            </div>
                          </details>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>
            ))}
          </div>
        </motion.div>
      )}

      {/* User Search Activity */}
      <h2 className="text-2xl font-bold mb-4">User Search Activity</h2>
      
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

