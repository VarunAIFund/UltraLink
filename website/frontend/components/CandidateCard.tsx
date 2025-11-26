import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  HiLocationMarker,
  HiUser,
  HiBriefcase,
  HiUserGroup,
  HiSparkles,
  HiPencil,
} from "react-icons/hi";
import type { CandidateResult, Highlight } from "@/lib/api";
import {
  generateHighlights,
  getNoteForCandidate,
  updateNoteForCandidate,
} from "@/lib/api";
import { motion } from "framer-motion";
import { CandidateHighlights } from "./CandidateHighlights";
import { IntroductionEmailDialog } from "./IntroductionEmailDialog";
import { generateIntroductionEmail, sendIntroductionEmail } from "@/lib/api";

interface CandidateCardProps {
  candidate: CandidateResult;
  searchQuery?: string;
}

export function CandidateCard({ candidate, searchQuery }: CandidateCardProps) {
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [showHighlights, setShowHighlights] = useState(false);
  const [loadingHighlights, setLoadingHighlights] = useState(false);
  const [highlightsError, setHighlightsError] = useState<string | null>(null);

  // Profile picture error state
  const [imageError, setImageError] = useState(false);

  // Notes state
  const [note, setNote] = useState<string>("");
  const [originalNote, setOriginalNote] = useState<string>("");
  const [showNotes, setShowNotes] = useState(false);
  const [loadingNote, setLoadingNote] = useState(false);
  const [savingNote, setSavingNote] = useState(false);
  const [noteError, setNoteError] = useState<string | null>(null);
  const [noteLoaded, setNoteLoaded] = useState(false);
  const [isEditingNote, setIsEditingNote] = useState(false);
  const [isHoveringNote, setIsHoveringNote] = useState(false);

  // Email introduction state
  const [showEmailDialog, setShowEmailDialog] = useState(false);
  const [selectedConnection, setSelectedConnection] = useState<string>("");

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
      console.error("Error generating highlights:", error);
      setHighlightsError("Failed to generate insights. Please try again.");
      setShowHighlights(false);
    } finally {
      setLoadingHighlights(false);
    }
  };

  const handleToggleNotes = async () => {
    // If already showing, just hide
    if (showNotes) {
      setShowNotes(false);
      return;
    }

    // If we already loaded the note, just show it
    if (noteLoaded) {
      setShowNotes(true);
      return;
    }

    // Otherwise, fetch the note first, then show
    setLoadingNote(true);
    setNoteError(null);

    try {
      const response = await getNoteForCandidate(candidate.linkedin_url);
      const loadedNote = response.note || "";
      setNote(loadedNote);
      setOriginalNote(loadedNote);
      setNoteLoaded(true);
      // Always start in view mode
      setIsEditingNote(false);
      // Only show notes after data is loaded
      setShowNotes(true);
    } catch (error) {
      console.error("Error loading note:", error);
      setNoteError("Failed to load note. Please try again.");
    } finally {
      setLoadingNote(false);
    }
  };

  const handleNoteBlur = async () => {
    // Only save if content has changed
    if (note !== originalNote) {
      setSavingNote(true);
      setNoteError(null);

      try {
        await updateNoteForCandidate(candidate.linkedin_url, note);
        setOriginalNote(note); // Update original to new saved value
      } catch (error) {
        console.error("Error saving note:", error);
        setNoteError("Failed to save note. Please try again.");
        // Revert to original note on error
        setNote(originalNote);
      } finally {
        setSavingNote(false);
      }
    }

    // Always exit edit mode on blur
    setIsEditingNote(false);
  };

  const handleNoteFocus = () => {
    setIsEditingNote(true);
    setNoteError(null);
  };

  const handleCancelNote = () => {
    setShowNotes(false);
    setNoteError(null);
  };
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{
        y: -4,
        boxShadow:
          "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
      }}
    >
      <Card className="h-full transition-all duration-200">
        <CardHeader>
          <div className="flex justify-between items-start gap-4">
            <div className="flex gap-4 flex-1 items-center">
              {candidate.profile_pic && !imageError ? (
                <img
                  src={candidate.profile_pic}
                  alt={candidate.name}
                  className="w-16 h-16 rounded-full object-cover flex-shrink-0"
                  onError={() => setImageError(true)}
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
            {candidate.match === "strong" &&
              candidate.relevance_score !== null &&
              candidate.relevance_score !== undefined && (
                <div className="text-right">
                  <div className="text-2xl font-bold text-primary">
                    {candidate.relevance_score}
                  </div>
                  <div className="text-xs text-muted-foreground">Score</div>
                </div>
              )}
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
                <span>
                  Mutual Connections ({candidate.connected_to.length})
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {candidate.connected_to.slice(0, 10).map((connection, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      // Capitalize first letter of connection name
                      const capitalizedConnection = connection.charAt(0).toUpperCase() + connection.slice(1);
                      setSelectedConnection(capitalizedConnection);
                      setShowEmailDialog(true);
                    }}
                    className="bg-muted text-muted-foreground px-2 py-1 rounded text-xs hover:bg-primary hover:text-primary-foreground transition-colors cursor-pointer"
                  >
                    {connection}
                  </button>
                ))}
                {candidate.connected_to.length > 10 && (
                  <span className="text-xs text-muted-foreground px-2 py-1">
                    +{candidate.connected_to.length - 10} more
                  </span>
                )}
              </div>
            </div>
          )}
          <div className="flex items-center gap-3 mt-4 flex-wrap">
            <a
              href={candidate.linkedin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline"
            >
              View LinkedIn Profile →
            </a>
            <div className="ml-auto flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleToggleNotes}
                disabled={loadingNote}
              >
                <HiPencil className="w-4 h-4 mr-2" />
                {loadingNote
                  ? "Loading..."
                  : showNotes
                  ? "Hide Notes"
                  : "Notes"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleToggleHighlights}
                disabled={loadingHighlights}
              >
                <HiSparkles className="w-4 h-4 mr-2" />
                {loadingHighlights
                  ? "Loading..."
                  : showHighlights
                  ? "Hide AI Insights"
                  : "AI Insights"}
              </Button>
            </div>
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

          {showNotes && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 border-t pt-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium">Notes</h4>
                  {savingNote && (
                    <span className="text-sm text-muted-foreground">
                      Saving...
                    </span>
                  )}
                </div>
                <div
                  className="relative"
                  onMouseEnter={() => !isEditingNote && setIsHoveringNote(true)}
                  onMouseLeave={() => setIsHoveringNote(false)}
                >
                  <Textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    onFocus={handleNoteFocus}
                    onBlur={handleNoteBlur}
                    placeholder="Click to add notes about this candidate..."
                    className="min-h-[100px] resize-y"
                    disabled={savingNote}
                    readOnly={!isEditingNote}
                  />
                  {!isEditingNote && isHoveringNote && (
                    <div className="absolute inset-0 bg-black/5 rounded-md flex items-center justify-center cursor-text pointer-events-none">
                      <span className="text-sm text-muted-foreground font-medium">
                        Click to edit
                      </span>
                    </div>
                  )}
                </div>
                {noteError && (
                  <p className="text-sm text-destructive">{noteError}</p>
                )}
              </div>
            </motion.div>
          )}
        </CardContent>
      </Card>

      {/* Introduction Email Dialog */}
      <IntroductionEmailDialog
        open={showEmailDialog}
        onOpenChange={setShowEmailDialog}
        connectionName={selectedConnection}
        candidateName={candidate.name}
        onGenerate={async (fromEmail: string, senderName: string) => {
          const result = await generateIntroductionEmail(
            candidate,
            searchQuery || "Opportunity at AI Fund",
            selectedConnection,
            fromEmail,
            senderName
          );
          return { subject: result.subject, body: result.body };
        }}
        onSend={async (subject, body, fromEmail, senderName, toEmail) => {
          await sendIntroductionEmail(subject, body, fromEmail, senderName, toEmail);
        }}
      />
    </motion.div>
  );
}
