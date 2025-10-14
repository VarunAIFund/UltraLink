'use client';

import { useState } from 'react';
import { HiChevronDown } from 'react-icons/hi';

interface SqlDisplayProps {
  sql: string;
}

export function SqlDisplay({ sql }: SqlDisplayProps) {
  const [sqlOpen, setSqlOpen] = useState(false);

  if (!sql) return null;

  return (
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
  );
}
