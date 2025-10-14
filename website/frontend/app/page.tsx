'use client';

import { useState } from 'react';
import { searchAndRank, type CandidateResult } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { HiLocationMarker, HiUser, HiBriefcase, HiUserGroup, HiChevronDown } from 'react-icons/hi';

export default function Home() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<CandidateResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sql, setSql] = useState('');
  const [sqlOpen, setSqlOpen] = useState(false);

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

      <div className="flex gap-4 mb-8">
        <Input
          type="text"
          placeholder="Search for candidates (e.g., CEO in healthcare with startup experience)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="flex-1"
        />
        <Button onClick={handleSearch} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {sql && (
        <div className="mb-6 border rounded-lg overflow-hidden">
          <button
            onClick={() => setSqlOpen(!sqlOpen)}
            className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
          >
            <span className="font-medium">Generated SQL</span>
            <HiChevronDown
              className={`transition-transform duration-200 ${
                sqlOpen ? 'rotate-180' : ''
              }`}
            />
          </button>
          {sqlOpen && (
            <div className="border-t">
              <pre className="text-sm bg-muted p-4 overflow-x-auto">
                <code>{sql}</code>
              </pre>
            </div>
          )}
        </div>
      )}

      {results.length > 0 && (
        <div>
          <h2 className="text-2xl font-semibold mb-4">
            {results.length} Candidates Found
          </h2>
          <div className="grid gap-4">
            {results.map((candidate, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex gap-4 flex-1">
                      {candidate.profile_pic ? (
                        <img
                          src={candidate.profile_pic}
                          alt={candidate.name}
                          className="w-16 h-16 rounded-full object-cover flex-shrink-0"
                        />
                      ) : (
                        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                          <HiUser className="w-8 h-8 text-muted-foreground" />
                        </div>
                      )}
                      <div className="flex-1">
                        <CardTitle>{candidate.name}</CardTitle>
                        <CardDescription>{candidate.headline}</CardDescription>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-primary">
                        {candidate.relevance_score}
                      </div>
                      <div className="text-xs text-muted-foreground">Score</div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm mb-4">{candidate.fit_description}</p>
                  <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                    {candidate.location && (
                      <span className="flex items-center gap-1">
                        <HiLocationMarker /> {candidate.location}
                      </span>
                    )}
                    {candidate.seniority && (
                      <span className="flex items-center gap-1">
                        <HiUser /> {candidate.seniority}
                      </span>
                    )}
                    {candidate.years_experience && (
                      <span className="flex items-center gap-1">
                        <HiBriefcase /> {candidate.years_experience} years
                      </span>
                    )}
                  </div>
                  {candidate.skills && candidate.skills.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-4">
                      {candidate.skills.slice(0, 5).map((skill, i) => (
                        <span
                          key={i}
                          className="bg-secondary text-secondary-foreground px-2 py-1 rounded text-xs"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
                  {candidate.connected_to && candidate.connected_to.length > 0 && (
                    <div className="mt-4 border-t pt-4">
                      <div className="flex items-center gap-2 text-sm font-medium mb-2">
                        <HiUserGroup className="text-muted-foreground" />
                        <span>Mutual Connections ({candidate.connected_to.length})</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {candidate.connected_to.slice(0, 10).map((connection, i) => (
                          <span
                            key={i}
                            className="bg-muted text-muted-foreground px-2 py-1 rounded text-xs"
                          >
                            {connection}
                          </span>
                        ))}
                        {candidate.connected_to.length > 10 && (
                          <span className="text-xs text-muted-foreground px-2 py-1">
                            +{candidate.connected_to.length - 10} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  <a
                    href={candidate.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-4 text-sm text-primary hover:underline"
                  >
                    View LinkedIn Profile →
                  </a>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
