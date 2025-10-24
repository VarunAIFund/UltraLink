"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { searchAndRank, getSearchSession, type CandidateResult } from "@/lib/api";
import { SearchBar } from "@/components/SearchBar";
import { SqlDisplay } from "@/components/SqlDisplay";
import { CandidateList } from "@/components/CandidateList";
import { motion } from "framer-motion";

export default function Home() {
  const pathname = usePathname();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CandidateResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sql, setSql] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [connectedTo, setConnectedTo] = useState("all");

  // Load saved search if URL contains /search/[id]
  useEffect(() => {
    const loadSavedSearch = async () => {
      const searchIdMatch = pathname.match(/^\/search\/([a-f0-9-]+)$/);
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
        } catch (err) {
          setError(err instanceof Error ? err.message : "Failed to load search");
        } finally {
          setLoading(false);
        }
      }
    };

    loadSavedSearch();
  }, [pathname]);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setResults([]);
    setSql("");
    setHasSearched(false);

    try {
      const response = await searchAndRank(query, connectedTo);
      setResults(response.results);
      setSql(response.sql);
      setHasSearched(true);

      // Update URL with search ID without page reload
      if (response.id) {
        window.history.pushState({}, "", `/search/${response.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8 max-w-5xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8 mt-12 text-center"
      >
        <h1 className="text-5xl font-bold mb-2">UltraLink</h1>
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
      />
    </div>
  );
}
