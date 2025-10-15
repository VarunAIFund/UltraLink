import type { CandidateResult } from '@/lib/api';
import { CandidateCard } from './CandidateCard';
import { CandidateCardSkeleton } from './CandidateCardSkeleton';
import { EmptyState } from './EmptyState';

interface CandidateListProps {
  results: CandidateResult[];
  hasSearched: boolean;
  loading?: boolean;
}

export function CandidateList({ results, hasSearched, loading }: CandidateListProps) {
  // Show empty state before first search
  if (!hasSearched && !loading) {
    return <EmptyState />;
  }

  return (
    <div>
      {loading ? (
        <>
          <h2 className="text-2xl font-semibold mb-4">Searching...</h2>
          <div className="grid gap-4">
            {[1, 2, 3].map((i) => (
              <CandidateCardSkeleton key={i} />
            ))}
          </div>
        </>
      ) : (
        <>
          <h2 className="text-2xl font-semibold mb-4">
            {results.length} Candidates Found
          </h2>
          {results.length > 0 && (
            <div className="grid gap-4">
              {results.map((candidate, index) => (
                <CandidateCard key={index} candidate={candidate} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
