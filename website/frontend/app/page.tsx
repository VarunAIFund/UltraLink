'use client';

import { useState } from 'react';
import { searchAndRank, type CandidateResult } from '@/lib/api';
import { SearchBar } from '@/components/SearchBar';
import { SqlDisplay } from '@/components/SqlDisplay';
import { CandidateList } from '@/components/CandidateList';

export default function Home() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<CandidateResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sql, setSql] = useState('');

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setResults([]);
    setSql('');

    try {
      const response = await searchAndRank(query);
      setResults(response.results);
      setSql(response.sql);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">UltraLink Search</h1>
        <p className="text-muted-foreground">AI-powered candidate search and ranking</p>
      </div>

      <SearchBar
        query={query}
        setQuery={setQuery}
        onSearch={handleSearch}
        loading={loading}
      />

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <SqlDisplay sql={sql} />

      <CandidateList results={results} />
    </div>
  );
}
