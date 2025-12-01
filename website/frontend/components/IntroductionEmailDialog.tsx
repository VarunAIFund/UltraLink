"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { HiMail, HiCheck, HiX } from "react-icons/hi";

interface IntroductionEmailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  connectionName: string;
  candidateName: string;
  onGenerate: (
    fromEmail: string,
    senderName: string
  ) => Promise<{ subject: string; body: string }>;
  onSend: (
    subject: string,
    body: string,
    fromEmail: string,
    senderName: string,
    toEmail: string
  ) => Promise<void>;
}

const SENDER_OPTIONS = [
  { label: "Linda", value: "linda", email: "linda@aifund.ai" },
  { label: "Jon", value: "jon", email: "jon@aifund.ai" },
  { label: "Juliana", value: "juliana", email: "juliana@aifund.ai" },
  { label: "Luisana", value: "luisana", email: "varun@aifund.ai" },
  { label: "Mary", value: "mary", email: "mary@aifund.ai" },
];

// Map connection names to their email addresses
const RECEIVER_EMAILS: Record<string, string> = {
  dan: "dan@aifund.ai",
  linda: "linda@aifund.ai",
  jon: "jon@aifund.ai",
  mary: "mary@aifund.ai",
  andy: "andy@aifund.ai",
  eli: "eli@aifund.ai",
  katherine: "katherine@aifund.ai",
  rishabh: "rishabh@aifund.ai",
};

export function IntroductionEmailDialog({
  open,
  onOpenChange,
  connectionName,
  candidateName,
  onGenerate,
  onSend,
}: IntroductionEmailDialogProps) {
  const [selectedSender, setSelectedSender] = useState("linda");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [bodyHtml, setBodyHtml] = useState(""); // Store original HTML
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Convert HTML to plain text for display
  const htmlToPlainText = (html: string): string => {
    return html
      .replace(/<p>/g, "")
      .replace(/<\/p>/g, "\n\n")
      .replace(/<br\s*\/?>/g, "\n")
      .replace(/<a[^>]*href="([^"]*)"[^>]*>([^<]*)<\/a>/g, "$2 ($1)")
      .replace(/<[^>]*>/g, "")
      .trim();
  };

  // Convert plain text back to HTML for sending
  const plainTextToHtml = (text: string): string => {
    return text
      .split("\n\n")
      .filter((para) => para.trim())
      .map((para) => `<p>${para.replace(/\n/g, "<br>")}</p>`)
      .join("");
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setGenerated(false);

    try {
      const sender = SENDER_OPTIONS.find((s) => s.value === selectedSender);
      const result = await onGenerate(
        sender?.email || "linda@aifund.ai",
        sender?.label || "Linda"
      );
      setSubject(result.subject);
      setBodyHtml(result.body); // Store original HTML
      setBody(htmlToPlainText(result.body)); // Convert to plain text for display
      setGenerated(true);
    } catch (err) {
      console.error("Failed to generate email:", err);
      setError(err instanceof Error ? err.message : "Failed to generate email");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    setSending(true);
    setError(null);

    try {
      // Convert plain text back to HTML for sending
      const htmlToSend = plainTextToHtml(body);
      const sender = SENDER_OPTIONS.find((s) => s.value === selectedSender);

      // Get receiver email from connection name
      const receiverEmail =
        RECEIVER_EMAILS[connectionName.toLowerCase()] || "varun@aifund.ai";

      await onSend(
        subject,
        htmlToSend,
        sender?.email || "Linda@aifund.ai",
        sender?.label || "Linda",
        receiverEmail
      );
      setSent(true);
      // Auto-close after 2 seconds
      setTimeout(() => {
        onOpenChange(false);
        // Reset state when dialog closes
        setTimeout(() => {
          setSelectedSender("linda");
          setSubject("");
          setBody("");
          setBodyHtml("");
          setGenerated(false);
          setSent(false);
        }, 300);
      }, 2000);
    } catch (err) {
      console.error("Failed to send email:", err);
      setError(err instanceof Error ? err.message : "Failed to send email");
    } finally {
      setSending(false);
    }
  };

  const handleClose = () => {
    onOpenChange(false);
    // Reset state after dialog close animation
    setTimeout(() => {
      setSelectedSender("linda");
      setSubject("");
      setBody("");
      setBodyHtml("");
      setGenerated(false);
      setSent(false);
      setError(null);
    }, 300);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            <div className="flex items-center gap-2">
              <HiMail className="w-5 h-5" />
              <span>Introduction Request via {connectionName}</span>
            </div>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {!generated && !loading && (
            <div className="text-center py-6">
              <p className="text-muted-foreground mb-6">
                Click the button below to generate a personalized introduction
                email asking {connectionName} to introduce you to{" "}
                {candidateName}.
              </p>
              <div className="flex flex-col items-center gap-4">
                <div className="flex items-center gap-3">
                  <Label htmlFor="from-select" className="text-sm font-medium">
                    From:
                  </Label>
                  <Select
                    value={selectedSender}
                    onValueChange={setSelectedSender}
                  >
                    <SelectTrigger id="from-select" className="w-[240px]">
                      <SelectValue>
                        {
                          SENDER_OPTIONS.find((s) => s.value === selectedSender)
                            ?.label
                        }{" "}
                        &lt;
                        {
                          SENDER_OPTIONS.find((s) => s.value === selectedSender)
                            ?.email
                        }
                        &gt;
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {SENDER_OPTIONS.map((sender) => (
                        <SelectItem key={sender.value} value={sender.value}>
                          {sender.label} &lt;{sender.email}&gt;
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  onClick={handleGenerate}
                  size="lg"
                  className="shadow-sm"
                >
                  <HiMail className="w-4 h-4 mr-2" />
                  Generate Email
                </Button>
              </div>
            </div>
          )}

          {loading && (
            <div className="text-center py-8">
              <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-muted-foreground">
                Generating personalized email...
              </p>
            </div>
          )}

          {generated && !sent && (
            <>
              <div className="space-y-2">
                <Label htmlFor="subject">Subject</Label>
                <Input
                  id="subject"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="Email subject"
                  disabled={sending}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="body">Email Body</Label>
                <Textarea
                  id="body"
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  placeholder="Email body"
                  rows={12}
                  className="text-sm"
                  disabled={sending}
                />
                <p className="text-xs text-muted-foreground">
                  Edit the email text. Double line breaks create new paragraphs.
                </p>
              </div>
            </>
          )}

          {sent && (
            <div className="text-center py-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full mb-4">
                <HiCheck className="w-8 h-8 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Email Sent!</h3>
              <p className="text-muted-foreground">
                Email sent to {connectionName} at{" "}
                {RECEIVER_EMAILS[connectionName.toLowerCase()] ||
                  "varun@aifund.ai"}
              </p>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
              <HiX className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-destructive">Error</p>
                <p className="text-sm text-destructive/80">{error}</p>
              </div>
            </div>
          )}
        </div>

        {generated && !sent && (
          <DialogFooter>
            <Button variant="outline" onClick={handleClose} disabled={sending}>
              Cancel
            </Button>
            <Button
              onClick={handleSend}
              disabled={sending || !subject || !body}
            >
              {sending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  Sending...
                </>
              ) : (
                <>
                  <HiMail className="w-4 h-4 mr-2" />
                  Send Email
                </>
              )}
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
