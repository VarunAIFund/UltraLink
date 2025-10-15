import type { CandidateResult } from '@/lib/api';
import { CandidateCard } from './CandidateCard';

interface CandidateListProps {
  results: CandidateResult[];
  hasSearched: boolean;
}

export function CandidateList({ results, hasSearched }: CandidateListProps) {
  if (!hasSearched) return null;

  return (
    <div>
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
    </div>
  );
}
