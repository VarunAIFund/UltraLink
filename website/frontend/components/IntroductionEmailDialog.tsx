"use client";

import { useState, useEffect } from "react";
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
import { HiMail, HiCheck, HiX } from "react-icons/hi";
import { getUser, getReceiver, type User, type Receiver } from "@/lib/api";

interface IntroductionEmailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  connectionName: string;
  candidateName: string;
  currentUserName: string; // Username of current user
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

export function IntroductionEmailDialog({
  open,
  onOpenChange,
  connectionName,
  candidateName,
  currentUserName,
  onGenerate,
  onSend,
}: IntroductionEmailDialogProps) {
  // Fetch current user (from users table) and receiver (from receivers table)
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [receiverUser, setReceiverUser] = useState<Receiver | null>(null);
  const [loadingUsers, setLoadingUsers] = useState(true);

  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [bodyHtml, setBodyHtml] = useState(""); // Store original HTML
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch current user and receiver user info
  useEffect(() => {
    const fetchUsers = async () => {
      setLoadingUsers(true);
      setCurrentUser(null);
      setReceiverUser(null);

      try {
        console.log('[EMAIL DIALOG] Fetching users:', {
          currentUserName,
          connectionName,
          currentUserNameLower: currentUserName.toLowerCase(),
          connectionNameLower: connectionName.toLowerCase()
        });

        // Fetch current user from users table, receiver from receivers table
        const [currentUserRes, receiverRes] = await Promise.all([
          getUser(currentUserName.toLowerCase()),
          getReceiver(connectionName.toLowerCase())
        ]);

        console.log('[EMAIL DIALOG] Fetch results:', {
          currentUserSuccess: currentUserRes.success,
          receiverSuccess: receiverRes.success
        });

        if (currentUserRes.success) {
          setCurrentUser(currentUserRes.user);
        }
        if (receiverRes.success) {
          setReceiverUser(receiverRes.receiver);
        }
      } catch (err) {
        console.error("Failed to fetch user info:", err);
        setError("Failed to load user information. Please try again.");
      } finally {
        setLoadingUsers(false);
      }
    };

    if (open && currentUserName && connectionName) {
      fetchUsers();
    } else if (open) {
      // Dialog opened but missing user info
      console.log('[EMAIL DIALOG] Dialog opened without user info:', {
        currentUserName,
        connectionName
      });
      setLoadingUsers(false);
    }
  }, [open, currentUserName, connectionName]);

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
    if (!currentUser) return;

    setLoading(true);
    setError(null);
    setGenerated(false);

    try {
      const result = await onGenerate(
        currentUser.email,
        currentUser.display_name
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
    if (!currentUser || !receiverUser) return;

    setSending(true);
    setError(null);

    try {
      // Convert plain text back to HTML for sending
      const htmlToSend = plainTextToHtml(body);

      await onSend(
        subject,
        htmlToSend,
        currentUser.email,
        currentUser.display_name,
        receiverUser.email
      );
      setSent(true);
      // Auto-close after 2 seconds
      setTimeout(() => {
        onOpenChange(false);
        // Reset state when dialog closes
        setTimeout(() => {
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
              <p className="text-muted-foreground mb-2">
                Click the button below to generate a personalized introduction
                email asking {connectionName} to introduce you to{" "}
                {candidateName}.
              </p>
              {loadingUsers ? (
                <p className="text-sm text-muted-foreground mb-6">
                  Loading user information...
                </p>
              ) : currentUser ? (
                <p className="text-sm text-muted-foreground mb-6">
                  From: {currentUser.display_name} &lt;{currentUser.email}&gt;
                </p>
              ) : (
                <p className="text-sm text-destructive mb-6">
                  Unable to load user information
                </p>
              )}
              <Button
                onClick={handleGenerate}
                size="lg"
                className="shadow-sm"
                disabled={loadingUsers || !currentUser}
              >
                <HiMail className="w-4 h-4 mr-2" />
                Generate Email
              </Button>
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
                Email sent to {receiverUser?.display_name || connectionName} at{" "}
                {receiverUser?.email || ""}
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
