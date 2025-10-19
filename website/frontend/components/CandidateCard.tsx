import { useState } from 'react';
import Image from 'next/image';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  HiLocationMarker,
  HiUser,
  HiBriefcase,
  HiUserGroup,
  HiSparkles,
} from "react-icons/hi";
import type { CandidateResult, Highlight } from "@/lib/api";
import { generateHighlights } from "@/lib/api";
import { motion } from "framer-motion";
import { CandidateHighlights } from "./CandidateHighlights";

interface CandidateCardProps {
  candidate: CandidateResult;
}

export function CandidateCard({ candidate }: CandidateCardProps) {
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [showHighlights, setShowHighlights] = useState(false);
  const [loadingHighlights, setLoadingHighlights] = useState(false);
  const [highlightsError, setHighlightsError] = useState<string | null>(null);

  const handleToggleHighlights = async () => {
    // If already showing, just hide
    if (showHighlights) {
      setShowHighlights(false);
      return;
    }

    // If we already have highlights cached, just show them
    if (highlights.length > 0) {
      setShowHighlights(true);
      return;
    }

    // Otherwise, fetch highlights
    setLoadingHighlights(true);
    setHighlightsError(null);
    setShowHighlights(true);

    try {
      const response = await generateHighlights(candidate);
      setHighlights(response.highlights);
    } catch (error) {
      console.error('Error generating highlights:', error);
      setHighlightsError('Failed to generate insights. Please try again.');
      setShowHighlights(false);
    } finally {
      setLoadingHighlights(false);
    }
  };
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ y: -4, boxShadow: "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)" }}
    >
      <Card className="h-full transition-all duration-200">
      <CardHeader>
        <div className="flex justify-between items-start gap-4">
          <div className="flex gap-4 flex-1 items-center">
            {candidate.profile_pic ? (
              <Image
                src={candidate.profile_pic}
                alt={candidate.name}
                width={64}
                height={64}
                className="w-16 h-16 rounded-full object-cover flex-shrink-0"
              />
            ) : (
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                <HiUser className="w-8 h-8 text-muted-foreground" />
              </div>
            )}
            <div className="flex-1">
              <CardTitle>{candidate.name}</CardTitle>
              <CardDescription>{candidate.headline}</CardDescription>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-primary">
              {candidate.relevance_score}
            </div>
            <div className="text-xs text-muted-foreground">Score</div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm mb-4">{candidate.fit_description}</p>
        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          {candidate.location && (
            <span className="flex items-center gap-1">
              <HiLocationMarker /> {candidate.location}
            </span>
          )}
          {candidate.seniority && (
            <span className="flex items-center gap-1">
              <HiUser /> {candidate.seniority}
            </span>
          )}
          {candidate.years_experience && (
            <span className="flex items-center gap-1">
              <HiBriefcase /> {candidate.years_experience} years
            </span>
          )}
        </div>
        {candidate.skills && candidate.skills.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            {candidate.skills.slice(0, 5).map((skill, i) => (
              <span
                key={i}
                className="bg-secondary text-secondary-foreground px-2 py-1 rounded text-xs"
              >
                {skill}
              </span>
            ))}
          </div>
        )}
        {candidate.connected_to && candidate.connected_to.length > 0 && (
          <div className="mt-4 border-t pt-4">
            <div className="flex items-center gap-2 text-sm font-medium mb-2">
              <HiUserGroup className="text-muted-foreground" />
              <span>Mutual Connections ({candidate.connected_to.length})</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {candidate.connected_to.slice(0, 10).map((connection, i) => (
                <span
                  key={i}
                  className="bg-muted text-muted-foreground px-2 py-1 rounded text-xs"
                >
                  {connection}
                </span>
              ))}
              {candidate.connected_to.length > 10 && (
                <span className="text-xs text-muted-foreground px-2 py-1">
                  +{candidate.connected_to.length - 10} more
                </span>
              )}
            </div>
          </div>
        )}
        <div className="flex items-center gap-3 mt-4">
          <a
            href={candidate.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary hover:underline"
          >
            View LinkedIn Profile →
          </a>
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleHighlights}
            disabled={loadingHighlights}
            className="ml-auto"
          >
            <HiSparkles className="w-4 h-4 mr-2" />
            {loadingHighlights
              ? 'Loading...'
              : showHighlights
              ? 'Hide AI Insights'
              : 'Show AI Insights'}
          </Button>
        </div>

        {highlightsError && (
          <p className="text-sm text-destructive mt-2">{highlightsError}</p>
        )}

        {showHighlights && (
          <CandidateHighlights
            highlights={highlights}
            loading={loadingHighlights}
          />
        )}
      </CardContent>
    </Card>
    </motion.div>
  );
}
