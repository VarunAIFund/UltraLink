import { motion, AnimatePresence } from 'framer-motion';
import { HiExternalLink, HiSparkles } from 'react-icons/hi';
import type { Highlight } from '@/lib/api';

interface CandidateHighlightsProps {
  highlights: Highlight[];
  loading: boolean;
}

export function CandidateHighlights({ highlights, loading }: CandidateHighlightsProps) {
  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        exit={{ opacity: 0, height: 0 }}
        className="mt-4 border-t pt-4"
      >
        <div className="flex items-center gap-2 mb-4">
          <HiSparkles className="text-primary animate-pulse" />
          <span className="text-sm font-medium text-muted-foreground">
            Generating AI insights...
          </span>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-20 bg-muted rounded-lg mb-2"></div>
              <div className="h-4 bg-muted rounded w-32"></div>
            </div>
          ))}
        </div>
      </motion.div>
    );
  }

  if (!highlights || highlights.length === 0) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        exit={{ opacity: 0, height: 0 }}
        transition={{ duration: 0.3 }}
        className="mt-4 border-t pt-4"
      >
        <div className="flex items-center gap-2 mb-4">
          <HiSparkles className="text-primary" />
          <span className="text-sm font-medium">AI-Generated Professional Insights</span>
        </div>

        <div className="space-y-3">
          {highlights.map((highlight, index) => (
            <motion.a
              key={index}
              href={highlight.url}
              target="_blank"
              rel="noopener noreferrer"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="block p-4 border rounded-lg hover:bg-accent hover:border-primary/50 transition-all cursor-pointer group"
            >
              <p className="text-sm text-foreground mb-3 leading-relaxed">
                {highlight.text}
              </p>
              <div className="flex items-center gap-2 text-xs text-primary">
                <HiExternalLink className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                <span className="font-medium">{highlight.source}</span>
              </div>
            </motion.a>
          ))}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
