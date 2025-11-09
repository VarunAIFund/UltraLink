import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectSeparator,
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
        <Select
          multiple
          options={[
            { label: 'Dan', value: 'dan' },
            { label: 'Linda', value: 'linda' },
            { label: 'Jon', value: 'jon' },
            { label: 'Mary', value: 'mary' },
          ]}
          value={connectedTo}
          onValueChange={setConnectedTo}
        >
          <SelectTrigger className="w-[140px] md:w-[180px]">
            <SelectValue placeholder="Connected to" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="dan">Dan</SelectItem>
            <SelectItem value="linda">Linda</SelectItem>
            <SelectItem value="jon">Jon</SelectItem>
            <SelectItem value="mary">Mary</SelectItem>
            <SelectSeparator />
            <button
              className="w-full px-2 py-1.5 text-sm text-left hover:bg-accent hover:text-accent-foreground rounded-sm cursor-pointer"
              onClick={() => setConnectedTo('')}
            >
              Deselect All
            </button>
          </SelectContent>
        </Select>
        <Button onClick={onSearch} disabled={loading} className="flex-1 md:flex-none">
          {loading ? 'Searching...' : 'Search'}
        </Button>
      </div>
    </div>
  );
}
