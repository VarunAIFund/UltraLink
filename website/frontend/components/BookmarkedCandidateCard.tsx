"use client";

import { useState } from "react";
import { Star, ExternalLink, User as UserIcon } from "lucide-react";
import { motion } from "framer-motion";
import type { Bookmark } from "@/lib/api";
import { removeBookmark } from "@/lib/api";

interface BookmarkedCandidateCardProps {
  bookmark: Bookmark;
  userName?: string;
  onRemove?: (bookmarkId: string) => void;
}

export function BookmarkedCandidateCard({
  bookmark,
  userName,
  onRemove,
}: BookmarkedCandidateCardProps) {
  const { candidate, linkedin_url } = bookmark;
  const [isRemoving, setIsRemoving] = useState(false);
  const [isRemoved, setIsRemoved] = useState(false);

  const handleRemoveBookmark = async () => {
    if (!userName || isRemoving) return;

    // Optimistic UI - immediately start exit animation
    setIsRemoving(true);
    setIsRemoved(true);

    try {
      await removeBookmark(userName, linkedin_url);
      // Notify parent to remove from state (no reload needed)
      onRemove?.(bookmark.id);
    } catch (error) {
      console.error("Error removing bookmark:", error);
      // Revert on error
      setIsRemoving(false);
      setIsRemoved(false);
    }
  };

  // Profile picture URL or fallback
  const profilePicUrl = candidate.profile_pic;

  // Don't render if removed
  if (isRemoved) {
    return (
      <motion.div
        initial={{ opacity: 1, scale: 1 }}
        animate={{ opacity: 0, scale: 0.8, height: 0, marginBottom: 0 }}
        transition={{ duration: 0.3 }}
        className="overflow-hidden"
      />
    );
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="relative bg-card border border-border rounded-xl shadow-sm hover:shadow-md transition-all p-6 flex flex-col h-full"
    >
      {/* Clickable Star Icon - Top Right */}
      <button
        onClick={handleRemoveBookmark}
        disabled={isRemoving}
        className="absolute top-4 right-4 hover:scale-110 transition-transform disabled:opacity-50"
        aria-label="Remove bookmark"
        title="Remove bookmark"
      >
        <Star
          className={`w-6 h-6 fill-primary text-primary ${
            isRemoving ? "animate-pulse" : ""
          }`}
        />
      </button>

      {/* Profile Picture */}
      <div className="mb-4">
        {profilePicUrl ? (
          <img
            src={profilePicUrl}
            alt={candidate.name}
            className="w-20 h-20 rounded-full object-cover bg-muted"
            onError={(e) => {
              // Fallback to icon if image fails
              const target = e.target as HTMLImageElement;
              target.style.display = "none";
              if (target.nextSibling) {
                (target.nextSibling as HTMLElement).style.display = "flex";
              }
            }}
          />
        ) : (
          <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center">
            <UserIcon className="w-10 h-10 text-muted-foreground" />
          </div>
        )}
        {/* Hidden fallback icon */}
        {profilePicUrl && (
          <div
            className="w-20 h-20 rounded-full bg-muted flex items-center justify-center"
            style={{ display: "none" }}
          >
            <UserIcon className="w-10 h-10 text-muted-foreground" />
          </div>
        )}
      </div>

      {/* Name */}
      <h3 className="text-lg font-semibold text-foreground mb-1 pr-8 line-clamp-2">
        {candidate.name}
      </h3>

      {/* Headline - Fixed height for 2 lines */}
      <p className="text-sm text-muted-foreground mb-4 line-clamp-2 h-10">
        {candidate.headline || " "}
      </p>

      {/* Spacer */}
      <div className="flex-grow" />

      {/* Divider */}
      <div className="border-t border-border my-4" />

      {/* View LinkedIn Profile Link */}
      <a
        href={linkedin_url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 text-primary hover:text-primary/80 text-sm font-medium transition-colors"
      >
        <span>View LinkedIn Profile</span>
        <ExternalLink className="w-4 h-4" />
      </a>
    </motion.div>
  );
}
