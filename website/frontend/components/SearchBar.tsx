import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface SearchBarProps {
  query: string;
  setQuery: (query: string) => void;
  onSearch: () => void;
  loading: boolean;
  connectedTo: string;
  setConnectedTo: (value: string) => void;
}

export function SearchBar({
  query,
  setQuery,
  onSearch,
  loading,
  connectedTo,
  setConnectedTo
}: SearchBarProps) {
  return (
    <div className="flex flex-col md:flex-row gap-3 mb-8">
      <Input
        type="text"
        placeholder="Search for candidates (e.g., CEO in healthcare with startup experience)"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && onSearch()}
        className="flex-1 w-full"
      />
      <div className="flex gap-3">
        <Select value={connectedTo} onValueChange={setConnectedTo}>
          <SelectTrigger className="w-[140px] md:w-[180px]">
            <SelectValue placeholder="Connected to" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="Dan">Dan</SelectItem>
            <SelectItem value="Linda">Linda</SelectItem>
            <SelectItem value="Jon">Jon</SelectItem>
            <SelectItem value="Mary">Mary</SelectItem>
          </SelectContent>
        </Select>
        <Button onClick={onSearch} disabled={loading} className="flex-1 md:flex-none">
          {loading ? 'Searching...' : 'Search'}
        </Button>
      </div>
    </div>
  );
}
