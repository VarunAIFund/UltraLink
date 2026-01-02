"use client";

import { useState, useMemo } from "react";
import type { CandidateResult } from "@/lib/api";
import { CandidateCard } from "./CandidateCard";
import { CandidateCardSkeleton } from "./CandidateCardSkeleton";
import { EmptyState } from "./EmptyState";
import { ChevronDown, ChevronRight } from "lucide-react";

interface CandidateListProps {
  results: CandidateResult[];
  hasSearched: boolean;
  loading?: boolean;
  searchStep?: string;
  searchStatus?: string;
  totalCost?: number;
  totalTime?: number;
  logs?: string;
  searchQuery?: string;
  userName?: string;
}

export function CandidateList({
  results,
  hasSearched,
  loading,
  searchStep,
  searchStatus,
  totalCost,
  totalTime,
  logs,
  searchQuery,
  userName,
}: CandidateListProps) {
  // Collapsible state for each section
  const [strongExpanded, setStrongExpanded] = useState(true);
  const [partialExpanded, setPartialExpanded] = useState(false);
  const [noMatchExpanded, setNoMatchExpanded] = useState(false);
  const [searchInfoExpanded, setSearchInfoExpanded] = useState(false);
  const [hideHired, setHideHired] = useState(false); // Default: show hired

  // Helper function to check if candidate is hired
  const isHired = (candidate: CandidateResult): boolean => {
    return candidate.lever_opportunities?.some((opp) => opp.hired) ?? false;
  };

  // Count of hired candidates (for display)
  const hiredCount = useMemo(() => {
    return results.filter((c) => isHired(c)).length;
  }, [results]);

  // Filter results based on hideHired toggle, then group by match type
  const groupedCandidates = useMemo(() => {
    const filteredResults = hideHired
      ? results.filter((c) => !isHired(c))
      : results;

    const strong = filteredResults
      .filter((c) => c.match === "strong")
      .sort((a, b) => {
        // Use relevance_score if available, otherwise use score (Stage 1 confidence)
        const scoreA = a.relevance_score ?? a.score ?? 0;
        const scoreB = b.relevance_score ?? b.score ?? 0;
        return scoreB - scoreA;
      });

    const partial = filteredResults
      .filter((c) => c.match === "partial")
      .sort((a, b) => {
        const scoreA = a.relevance_score ?? a.score ?? 0;
        const scoreB = b.relevance_score ?? b.score ?? 0;
        return scoreB - scoreA;
      });

    const noMatch = filteredResults
      .filter((c) => c.match === "no_match")
      .sort((a, b) => {
        const scoreA = a.relevance_score ?? a.score ?? 0;
        const scoreB = b.relevance_score ?? b.score ?? 0;
        return scoreB - scoreA;
      });

    return { strong, partial, noMatch };
  }, [results, hideHired]);

  // Show empty state before first search
  if (!hasSearched && !loading) {
    return <EmptyState />;
  }

  // Show loading skeleton if search is in progress
  const isSearchInProgress =
    loading ||
    (searchStatus && searchStatus !== "completed" && searchStatus !== "failed");

  if (isSearchInProgress) {
    return (
      <div>
        <h2 className="text-2xl font-semibold mb-4">
          {searchStep || "Searching..."}
        </h2>
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <CandidateCardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  // Total displayed candidates (after filtering)
  const displayedCount =
    groupedCandidates.strong.length +
    groupedCandidates.partial.length +
    groupedCandidates.noMatch.length;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold">
          {displayedCount} Candidates Found
          {hideHired && hiredCount > 0 && (
            <span className="text-sm font-normal text-muted-foreground ml-2">
              ({hiredCount} hired hidden)
            </span>
          )}
        </h2>
        {hiredCount > 0 && (
          <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
            <span className="text-muted-foreground">Hide hired</span>
            <button
              type="button"
              role="switch"
              aria-checked={hideHired}
              onClick={() => setHideHired(!hideHired)}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
                hideHired ? "bg-primary" : "bg-muted"
              }`}
            >
              <span
                className={`pointer-events-none block h-4 w-4 rounded-full bg-background shadow-lg ring-0 transition-transform ${
                  hideHired ? "translate-x-4" : "translate-x-0"
                }`}
              />
            </button>
          </label>
        )}
      </div>

      {displayedCount > 0 && (
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
                <h3 className="text-lg font-semibold">Strong Matches</h3>
                <span className="px-2 py-0.5 bg-muted text-muted-foreground text-sm font-medium rounded-full">
                  {groupedCandidates.strong.length}
                </span>
              </button>
              {strongExpanded && (
                <div className="space-y-4">
                  {groupedCandidates.strong.map((candidate, index) => (
                    <CandidateCard
                      key={index}
                      candidate={candidate}
                      searchQuery={searchQuery}
                      userName={userName}
                    />
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
                <h3 className="text-lg font-semibold">Partial Matches</h3>
                <span className="px-2 py-0.5 bg-muted text-muted-foreground text-sm font-medium rounded-full">
                  {groupedCandidates.partial.length}
                </span>
              </button>
              {partialExpanded && (
                <div className="space-y-4">
                  {groupedCandidates.partial.map((candidate, index) => (
                    <CandidateCard
                      key={index}
                      candidate={candidate}
                      searchQuery={searchQuery}
                      userName={userName}
                    />
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
                <h3 className="text-lg font-semibold">No Matches</h3>
                <span className="px-2 py-0.5 bg-muted text-muted-foreground text-sm font-medium rounded-full">
                  {groupedCandidates.noMatch.length}
                </span>
              </button>
              {noMatchExpanded && (
                <div className="space-y-4">
                  {groupedCandidates.noMatch.map((candidate, index) => (
                    <CandidateCard
                      key={index}
                      candidate={candidate}
                      searchQuery={searchQuery}
                      userName={userName}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Search Info Section */}
          {((totalCost !== undefined && totalCost > 0) ||
            (totalTime !== undefined && totalTime > 0) ||
            (logs && logs.length > 0)) && (
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
                <h3 className="text-lg font-semibold">Search Info</h3>
                {totalCost !== undefined && totalCost > 0 && (
                  <span className="px-2 py-0.5 bg-muted text-muted-foreground text-sm font-medium rounded-full">
                    ${totalCost.toFixed(4)}
                  </span>
                )}
                {totalTime !== undefined && totalTime > 0 && (
                  <span className="px-2 py-0.5 bg-muted text-muted-foreground text-sm font-medium rounded-full">
                    {Math.floor(totalTime / 60)} min{" "}
                    {Math.floor(totalTime % 60)} sec
                  </span>
                )}
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
                        {Math.floor(totalTime / 60)} min{" "}
                        {Math.floor(totalTime % 60)} sec
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
