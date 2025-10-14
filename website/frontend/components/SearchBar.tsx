import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface SearchBarProps {
  query: string;
  setQuery: (query: string) => void;
  onSearch: () => void;
  loading: boolean;
}

export function SearchBar({ query, setQuery, onSearch, loading }: SearchBarProps) {
  return (
    <div className="flex gap-4 mb-8">
      <Input
        type="text"
        placeholder="Search for candidates (e.g., CEO in healthcare with startup experience)"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && onSearch()}
        className="flex-1"
      />
      <Button onClick={onSearch} disabled={loading}>
        {loading ? 'Searching...' : 'Search'}
      </Button>
    </div>
  );
}
