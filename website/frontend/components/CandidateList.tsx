'use client';

import { useState, useMemo } from 'react';
import type { CandidateResult } from '@/lib/api';
import { CandidateCard } from './CandidateCard';
import { CandidateCardSkeleton } from './CandidateCardSkeleton';
import { EmptyState } from './EmptyState';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface CandidateListProps {
  results: CandidateResult[];
  hasSearched: boolean;
  loading?: boolean;
  totalCost?: number;
  totalTime?: number;
  logs?: string;
}

export function CandidateList({ results, hasSearched, loading, totalCost, totalTime, logs }: CandidateListProps) {
  // Collapsible state for each section
  const [strongExpanded, setStrongExpanded] = useState(true);
  const [partialExpanded, setPartialExpanded] = useState(false);
  const [noMatchExpanded, setNoMatchExpanded] = useState(false);
  const [searchInfoExpanded, setSearchInfoExpanded] = useState(false);

  // Group candidates by match type and sort by relevance_score (descending)
  const groupedCandidates = useMemo(() => {
    const strong = results
      .filter(c => c.match === 'strong')
      .sort((a, b) => b.relevance_score - a.relevance_score);

    const partial = results
      .filter(c => c.match === 'partial')
      .sort((a, b) => b.relevance_score - a.relevance_score);

    const noMatch = results
      .filter(c => c.match === 'no_match')
      .sort((a, b) => b.relevance_score - a.relevance_score);

    return { strong, partial, noMatch };
  }, [results]);

  // Show empty state before first search
  if (!hasSearched && !loading) {
    return <EmptyState />;
  }

  if (loading) {
    return (
      <div>
        <h2 className="text-2xl font-semibold mb-4">Searching...</h2>
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <CandidateCardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">
        {results.length} Candidates Found
      </h2>

      {results.length > 0 && (
        <div className="space-y-6">
          {/* Strong Matches Section */}
          {groupedCandidates.strong.length > 0 && (
            <div>
              <button
                onClick={() => setStrongExpanded(!strongExpanded)}
                className="w-full flex items-center gap-2 mb-4 px-4 py-3 border rounded-lg bg-card shadow-sm hover:shadow-md transition-shadow"
              >
                {strongExpanded ? (
                  <ChevronDown className="w-5 h-5" />
                ) : (
                  <ChevronRight className="w-5 h-5" />
                )}
                <h3 className="text-lg font-semibold">
                  Strong Matches
                </h3>
                <span className="px-2 py-0.5 bg-muted text-muted-foreground text-sm font-medium rounded-full">
                  {groupedCandidates.strong.length}
                </span>
              </button>
              {strongExpanded && (
                <div className="space-y-4">
                  {groupedCandidates.strong.map((candidate, index) => (
                    <CandidateCard key={index} candidate={candidate} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Partial Matches Section */}
          {groupedCandidates.partial.length > 0 && (
            <div>
              <button
                onClick={() => setPartialExpanded(!partialExpanded)}
                className="w-full flex items-center gap-2 mb-4 px-4 py-3 border rounded-lg bg-card shadow-sm hover:shadow-md transition-shadow"
              >
                {partialExpanded ? (
                  <ChevronDown className="w-5 h-5" />
                ) : (
                  <ChevronRight className="w-5 h-5" />
                )}
                <h3 className="text-lg font-semibold">
                  Partial Matches
                </h3>
                <span className="px-2 py-0.5 bg-muted text-muted-foreground text-sm font-medium rounded-full">
                  {groupedCandidates.partial.length}
                </span>
              </button>
              {partialExpanded && (
                <div className="space-y-4">
                  {groupedCandidates.partial.map((candidate, index) => (
                    <CandidateCard key={index} candidate={candidate} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* No Matches Section */}
          {groupedCandidates.noMatch.length > 0 && (
            <div>
              <button
                onClick={() => setNoMatchExpanded(!noMatchExpanded)}
                className="w-full flex items-center gap-2 mb-4 px-4 py-3 border rounded-lg bg-card shadow-sm hover:shadow-md transition-shadow"
              >
                {noMatchExpanded ? (
                  <ChevronDown className="w-5 h-5" />
                ) : (
                  <ChevronRight className="w-5 h-5" />
                )}
                <h3 className="text-lg font-semibold">
                  No Matches
                </h3>
                <span className="px-2 py-0.5 bg-muted text-muted-foreground text-sm font-medium rounded-full">
                  {groupedCandidates.noMatch.length}
                </span>
              </button>
              {noMatchExpanded && (
                <div className="space-y-4">
                  {groupedCandidates.noMatch.map((candidate, index) => (
                    <CandidateCard key={index} candidate={candidate} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Search Info Section */}
          {((totalCost !== undefined && totalCost > 0) || (totalTime !== undefined && totalTime > 0) || (logs && logs.length > 0)) && (
            <div>
              <button
                onClick={() => setSearchInfoExpanded(!searchInfoExpanded)}
                className="w-full flex items-center gap-2 mb-4 px-4 py-3 border rounded-lg bg-card shadow-sm hover:shadow-md transition-shadow"
              >
                {searchInfoExpanded ? (
                  <ChevronDown className="w-5 h-5" />
                ) : (
                  <ChevronRight className="w-5 h-5" />
                )}
                <h3 className="text-lg font-semibold">
                  Search Info
                </h3>
              </button>
              {searchInfoExpanded && (
                <div className="px-4 py-3 border rounded-lg bg-card space-y-4">
                  {totalCost !== undefined && totalCost > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Total Cost:</span>
                      <span className="font-mono font-semibold">
                        ${totalCost.toFixed(4)}
                      </span>
                    </div>
                  )}
                  {totalTime !== undefined && totalTime > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Total Time:</span>
                      <span className="font-mono font-semibold">
                        {Math.floor(totalTime / 60)} min {Math.floor(totalTime % 60)} sec
                      </span>
                    </div>
                  )}
                  {logs && logs.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-muted-foreground mb-2">
                        Execution Logs:
                      </h4>
                      <pre className="text-xs font-mono bg-muted p-3 rounded overflow-x-auto max-h-96 overflow-y-auto whitespace-pre-wrap break-words">
                        {logs}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
