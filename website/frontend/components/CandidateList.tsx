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
}

export function CandidateList({ results, hasSearched, loading }: CandidateListProps) {
  // Collapsible state for each section
  const [strongExpanded, setStrongExpanded] = useState(true);
  const [partialExpanded, setPartialExpanded] = useState(true);
  const [noMatchExpanded, setNoMatchExpanded] = useState(false);

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
        </div>
      )}
    </div>
  );
}
