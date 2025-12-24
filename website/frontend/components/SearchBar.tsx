"use client";

import { useState, useRef, useEffect } from "react";
import { User, ArrowRight, Zap } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getUser, getAllReceivers, type Receiver } from "@/lib/api";

interface SearchBarProps {
  query: string;
  setQuery: (query: string) => void;
  onSearch: () => void;
  loading: boolean;
  connectedTo: string;
  setConnectedTo: (value: string) => void;
  ranking: boolean;
  setRanking: (value: boolean) => void;
  userName?: string;
}

export function SearchBar({
  query,
  setQuery,
  onSearch,
  loading,
  connectedTo,
  setConnectedTo,
  ranking,
  setRanking,
  userName,
}: SearchBarProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [userDisplayName, setUserDisplayName] = useState<string | null>(null);
  const [receivers, setReceivers] = useState<Receiver[]>([]);
  const [loadingReceivers, setLoadingReceivers] = useState(true);

  // Fetch receivers for connection filter
  useEffect(() => {
    getAllReceivers()
      .then((data) => {
        if (data.success) {
          setReceivers(data.receivers);
        }
      })
      .catch((err) => {
        console.error('Error fetching receivers:', err);
      })
      .finally(() => {
        setLoadingReceivers(false);
      });
  }, []);

  // Fetch user display name if userName is provided
  useEffect(() => {
    if (userName) {
      getUser(userName)
        .then((data) => {
          if (data.success) {
            setUserDisplayName(data.user.display_name);
          }
        })
        .catch((err) => {
          console.error('Error fetching user info:', err);
        });
    }
  }, [userName]);

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [query]);

  return (
    <div className="w-full max-w-4xl mx-auto mb-8">
      {/* Main Search Card */}
      <div className="bg-[#faf9f7] dark:bg-card rounded-3xl shadow-lg border border-border/50 p-6 md:p-8">
        {/* Search Input */}
        <div className="mb-6">
          <textarea
            ref={textareaRef}
            placeholder={
              userName && userDisplayName
                ? `Search ${userDisplayName}'s network with natural language`
                : "Search for candidates (e.g., CEO in healthcare with startup experience)"
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && !loading) {
                e.preventDefault();
                onSearch();
              }
            }}
            disabled={loading}
            rows={1}
            className="w-full text-base md:text-lg font-medium bg-transparent border-none outline-none text-foreground placeholder:text-muted-foreground/60 disabled:opacity-50 resize-none overflow-hidden"
          />
        </div>

        {/* Controls Row */}
        <div className="flex flex-wrap items-center gap-3 md:gap-4">
          {/* Ranking Mode Selection */}
          <div className="flex items-center gap-2 p-1 bg-muted/30 rounded-full border border-border/50">
            <button
              onClick={() => setRanking(false)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                !ranking
                  ? "bg-primary/10 text-primary shadow-sm border-2 border-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>Fast Response</span>
            </button>
            <button
              onClick={() => setRanking(true)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                ranking
                  ? "bg-primary/10 text-primary shadow-sm border-2 border-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <User className="w-4 h-4" />
              <span>Relevance Ranking</span>
            </button>
          </div>

          {/* Spacer to push dropdown and button to the right */}
          <div className="flex-1" />

          {/* Connection Dropdown */}
          <Select
            multiple
            options={receivers.map(r => ({ label: r.display_name, value: r.username }))}
            value={connectedTo}
            onValueChange={setConnectedTo}
          >
            <SelectTrigger className="w-[180px] md:w-[200px] h-11 rounded-full border-2 bg-background">
              <SelectValue placeholder={loadingReceivers ? "Loading..." : "Connected to"} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {receivers.map((receiver) => (
                <SelectItem key={receiver.username} value={receiver.username}>
                  {receiver.display_name}
                </SelectItem>
              ))}
              <SelectSeparator />
              <button
                className="w-full px-2 py-1.5 text-sm text-left hover:bg-accent hover:text-accent-foreground rounded-sm cursor-pointer"
                onClick={() => setConnectedTo("")}
              >
                Deselect All
              </button>
            </SelectContent>
          </Select>

          {/* Search Button */}
          <button
            onClick={onSearch}
            disabled={loading}
            className="w-14 h-14 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground flex items-center justify-center transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <ArrowRight className="w-6 h-6" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
