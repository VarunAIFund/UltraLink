"use client";

import { useState, useEffect } from "react";
import { useParams, usePathname } from "next/navigation";
import { searchAndRank, searchAndRankStream, getSearchSession, getUser, type CandidateResult } from "@/lib/api";
import { SearchBar } from "@/components/SearchBar";
import { SqlDisplay } from "@/components/SqlDisplay";
import { CandidateList } from "@/components/CandidateList";
import HamburgerMenu from "@/components/HamburgerMenu";
import Sidebar from "@/components/Sidebar";
import { motion } from "framer-motion";

// Helper function to get user-friendly status messages
function getStatusMessage(status: string): string {
  const messages: Record<string, string> = {
    'searching': 'Searching database...',
    'classifying': 'Analyzing candidates...',
    'ranking': 'Ranking matches...',
    'completed': 'Complete',
    'failed': 'Search failed'
  };
  return messages[status] || 'Processing...';
}

export default function UserSearchPage() {
  const params = useParams();
  const pathname = usePathname();
  const userName = params?.user as string;

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CandidateResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sql, setSql] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [connectedTo, setConnectedTo] = useState(userName || "all"); // Default to user's connections
  const [totalCost, setTotalCost] = useState<number>(0);
  const [totalTime, setTotalTime] = useState<number>(0);
  const [logs, setLogs] = useState<string>("");
  const [searchStep, setSearchStep] = useState<string>("");
  const [ranking, setRanking] = useState<boolean>(true);
  const [searchStatus, setSearchStatus] = useState<string>("completed");
  const [hasActiveSSE, setHasActiveSSE] = useState<boolean>(false);

  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // User display name
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

  // Load saved search if URL contains /user/search/[id] pattern
  useEffect(() => {
    const loadSavedSearch = async () => {
      // Match pattern: /[user]/search/[id]
      const searchIdMatch = pathname.match(/^\/[^/]+\/search\/([a-f0-9-]+)$/);
      if (searchIdMatch) {
        const searchId = searchIdMatch[1];
        setLoading(true);
        try {
          const response = await getSearchSession(searchId);
          setQuery(response.query);
          setResults(response.results);
          setSql(response.sql);
          setHasSearched(true);
          setConnectedTo(response.connected_to);
          setTotalCost(response.total_cost || 0);
          setTotalTime(response.total_time || 0);
          setLogs(response.logs || "");
          setRanking(response.ranking_enabled ?? true);
          setSearchStatus(response.status || "completed");

          // If search is still in progress, show appropriate message
          if (response.status && response.status !== "completed" && response.status !== "failed") {
            setLoading(true);
            setSearchStep(getStatusMessage(response.status));
          } else {
            setLoading(false);
          }
        } catch (err) {
          setError(err instanceof Error ? err.message : "Failed to load search");
          setLoading(false);
        }
      }
    };

    loadSavedSearch();
  }, [pathname]);

  // Poll for updates when search is in progress
  useEffect(() => {
    if (searchStatus !== "searching" && searchStatus !== "classifying" && searchStatus !== "ranking") {
      return;
    }

    if (hasActiveSSE) {
      console.log('[POLLING] Skipping poll - SSE connection is active');
      return;
    }

    const searchIdMatch = pathname.match(/^\/[^/]+\/search\/([a-f0-9-]+)$/);
    if (!searchIdMatch) {
      return;
    }

    const searchId = searchIdMatch[1];
    console.log('[POLLING] Starting poll for search', searchId);

    const pollInterval = setInterval(async () => {
      try {
        console.log('[POLLING] Checking status...');
        const response = await getSearchSession(searchId);

        setResults(response.results);
        setSql(response.sql);
        setTotalCost(response.total_cost || 0);
        setTotalTime(response.total_time || 0);
        setLogs(response.logs || "");

        const newStatus = response.status || "completed";

        if (newStatus !== searchStatus) {
          console.log('[POLLING] Status changed:', searchStatus, '→', newStatus);
          setSearchStatus(newStatus);
          setSearchStep(getStatusMessage(newStatus));
        }

        if (newStatus === "completed" || newStatus === "failed") {
          console.log('[POLLING] Search finished, stopping poll');
          setLoading(false);
          clearInterval(pollInterval);
        }
      } catch (err) {
        console.error('[POLLING] Error:', err);
      }
    }, 2000);

    return () => {
      console.log('[POLLING] Cleanup, stopping poll');
      clearInterval(pollInterval);
    };
  }, [pathname, loading, searchStatus, hasActiveSSE]);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setResults([]);
    setSql("");
    setHasSearched(false);
    setSearchStep("");
    setHasActiveSSE(true);

    try {
      const connectionFilter = connectedTo || 'all';

      const response = await searchAndRankStream(
        query,
        connectionFilter,
        ranking,
        (step: string, message: string) => {
          setSearchStep(message);
        },
        (searchId: string) => {
          console.log('[DEBUG] Search ID received early:', searchId);
          window.history.pushState({}, "", `/${userName}/search/${searchId}`);
        },
        userName // Pass userName to backend
      );

      setResults(response.results);
      setSql(response.sql);
      setHasSearched(true);
      setTotalCost(response.total_cost || 0);
      setTotalTime(response.total_time || 0);
      setLogs(response.logs || "");
      setSearchStep("");
      setSearchStatus("completed");

      if (response.id) {
        window.history.pushState({}, "", `/${userName}/search/${response.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setSearchStatus("failed");
    } finally {
      setLoading(false);
      setHasActiveSSE(false);
    }
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
        className="mb-8 mt-12 text-center"
      >
        <h1 className="text-5xl font-bold mb-2">
          {userDisplayName ? `${userDisplayName}'s Workspace` : 'UltraLink'}
        </h1>
        <p className="text-muted-foreground">
          AI-powered candidate search and ranking
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <SearchBar
          query={query}
          setQuery={setQuery}
          onSearch={handleSearch}
          loading={loading}
          connectedTo={connectedTo}
          setConnectedTo={setConnectedTo}
          ranking={ranking}
          setRanking={setRanking}
          userName={userName}
        />
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

      <SqlDisplay sql={sql} />

      <CandidateList
        results={results}
        hasSearched={hasSearched}
        loading={loading}
        searchStep={searchStep}
        searchStatus={searchStatus}
        totalCost={totalCost}
        totalTime={totalTime}
        logs={logs}
        searchQuery={query}
        userName={userName}
      />
    </div>
  );
}
