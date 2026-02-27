/**
 * API client for Flask backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

/**
 * Get the current Supabase session's access token for use in Authorization headers.
 * Returns null if the user is not authenticated.
 */
async function getAuthToken(): Promise<string | null> {
  try {
    const { createBrowserClient } = await import("./supabase");
    const supabase = createBrowserClient();
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  } catch {
    return null;
  }
}

/** Build auth headers for protected requests */
async function authHeaders(): Promise<Record<string, string>> {
  const token = await getAuthToken();
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

export interface Experience {
  org: string;
  company_url?: string;
  title: string;
  summary?: string;
  short_summary?: string;
  location?: string;
  company_skills?: string[];
  business_model?: string;
  product_type?: string;
  industry_tags?: string[];
}

export interface Education {
  school: string;
  degree?: string;
  field?: string;
}

export interface LeverOpportunity {
  url: string;
  hired: boolean;
}

export interface CandidateResult {
  name: string;
  linkedin_url: string;
  headline?: string;
  location?: string;
  match?: "strong" | "partial" | "no_match";
  relevance_score: number;
  fit_description: string;
  ranking_rationale?: string;
  stage_1_confidence?: number;
  score?: number; // Stage 1 confidence score used for sorting when ranking is off
  seniority?: string;
  years_experience?: number;
  skills?: string[];
  connected_to?: string[];
  profile_pic?: string;
  experiences?: Experience[];
  education?: Education[];
  notes?: string;
  lever_opportunities?: LeverOpportunity[];
  is_bookmarked?: boolean; // Bookmark status from database JOIN
}

export interface Highlight {
  text: string;
  source: string;
  url: string;
}

export interface HighlightsResponse {
  success: boolean;
  highlights: Highlight[];
  total_sources: number;
  error?: string;
}

export interface SearchResponse {
  success: boolean;
  id?: string;
  sql: string;
  results: CandidateResult[];
  total: number;
  total_cost?: number;
  total_time?: number;
  logs?: string;
  error?: string;
}

export interface SavedSearchResponse {
  success: boolean;
  id: string;
  query: string;
  connected_to: string;
  sql: string;
  results: CandidateResult[];
  total: number;
  total_cost?: number;
  total_time?: number;
  logs?: string;
  ranking_enabled?: boolean;
  status?: string;
  created_at: string;
  error?: string;
}

export async function searchAndRank(
  query: string,
  connectedTo?: string,
  userName?: string
): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/search-and-rank`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      connected_to: connectedTo || "all",
      user_name: userName,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function searchAndRankStream(
  query: string,
  connectedTo: string,
  ranking: boolean,
  onProgress: (step: string, message: string) => void,
  onSearchIdReceived?: (searchId: string) => void,
  userName?: string
): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/search-and-rank-stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      connected_to: connectedTo || "all",
      ranking: ranking,
      user_name: userName,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error("Response body is not readable");
  }

  let buffer = "";
  let finalData: SearchResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE messages (ending with \n\n)
    const messages = buffer.split("\n\n");
    buffer = messages.pop() || ""; // Keep incomplete message in buffer

    for (const message of messages) {
      if (!message.trim()) continue;

      // Parse SSE message (format: "data: {json}")
      const dataMatch = message.match(/^data: (.+)$/m);
      if (dataMatch) {
        try {
          const event = JSON.parse(dataMatch[1]);

          if (event.step === "complete" && event.data) {
            finalData = event.data;
          } else if (event.step === "error") {
            throw new Error(event.message);
          } else if (event.step === "search_created" && event.search_id) {
            // Search ID received - notify callback immediately
            if (onSearchIdReceived) {
              onSearchIdReceived(event.search_id);
            }
          } else {
            // Progress update
            onProgress(event.step, event.message);
          }
        } catch (e) {
          console.error("Failed to parse SSE message:", e);
        }
      }
    }
  }

  if (!finalData) {
    throw new Error("No final data received from server");
  }

  return finalData;
}

export async function generateHighlights(
  candidate: CandidateResult
): Promise<HighlightsResponse> {
  const response = await fetch(`${API_BASE_URL}/generate-highlights`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ candidate }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getSearchSession(
  searchId: string
): Promise<SavedSearchResponse> {
  const response = await fetch(`${API_BASE_URL}/search/${searchId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Search not found: ${response.statusText}`);
  }

  return response.json();
}

export async function healthCheck(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return response.json();
}

export interface NoteResponse {
  success: boolean;
  linkedin_url: string;
  note: string | null;
  error?: string;
}

export interface UpdateNoteResponse {
  success: boolean;
  message: string;
  linkedin_url: string;
  note: string;
  error?: string;
}

export async function getNoteForCandidate(
  linkedinUrl: string
): Promise<NoteResponse> {
  const encodedUrl = encodeURIComponent(linkedinUrl);
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/notes/${encodedUrl}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...auth,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function updateNoteForCandidate(
  linkedinUrl: string,
  note: string
): Promise<UpdateNoteResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/notes`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...auth,
    },
    body: JSON.stringify({
      linkedin_url: linkedinUrl,
      note: note,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export interface GenerateEmailResponse {
  success: boolean;
  subject: string;
  body: string;
  error?: string;
}

export interface SendEmailResponse {
  success: boolean;
  message: string;
  message_id?: string;
  error?: string;
}

export async function generateIntroductionEmail(
  candidate: CandidateResult,
  jobDescription: string,
  mutualConnectionName: string,
  fromEmail: string,
  senderName?: string
): Promise<GenerateEmailResponse> {
  const response = await fetch(`${API_BASE_URL}/generate-introduction-email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      candidate: candidate,
      job_description: jobDescription,
      mutual_connection_name: mutualConnectionName,
      sender_info: {
        name: senderName || "",
        role: "Partner",
        company: "AI Fund",
        email: fromEmail,
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function sendIntroductionEmail(
  subject: string,
  body: string,
  _fromEmail?: string,   // ignored — backend looks up sender from verified session
  _senderName?: string,  // ignored — backend looks up sender from verified session
  toEmail?: string
): Promise<SendEmailResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/send-introduction-email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...auth,
    },
    body: JSON.stringify({
      to_email: toEmail || "",
      subject: subject,
      body: body,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

// ========================
// USER MANAGEMENT API
// ========================

export interface User {
  username: string;
  display_name: string;
  email: string;
  role?: string;
}

export interface UsersResponse {
  success: boolean;
  users: User[];
  total: number;
  error?: string;
}

export interface UserResponse {
  success: boolean;
  user: User;
  error?: string;
}

export async function getAllUsers(): Promise<UsersResponse> {
  const response = await fetch(`${API_BASE_URL}/users`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getUser(userName: string): Promise<UserResponse> {
  const response = await fetch(`${API_BASE_URL}/users/${userName}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export interface UserWithRole extends User {
  role: string;
  secondary_emails?: string[];
}

export interface AdminUsersResponse {
  success: boolean;
  users: UserWithRole[];
  total: number;
  error?: string;
}

export interface AdminUserResponse {
  success: boolean;
  user: UserWithRole;
  error?: string;
}

export async function adminGetUsers(_requestingUser?: string): Promise<AdminUsersResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/users`, { headers: auth });
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

export async function adminCreateUser(
  _requestingUser: string,
  data: { username: string; display_name: string; email: string; role: string; secondary_emails?: string[] }
): Promise<AdminUserResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...auth },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.error || `API error: ${response.statusText}`);
  }
  return response.json();
}

export async function adminUpdateUser(
  _requestingUser: string,
  username: string,
  data: { display_name: string; email: string; role: string; secondary_emails?: string[] }
): Promise<AdminUserResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/users/${username}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...auth },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.error || `API error: ${response.statusText}`);
  }
  return response.json();
}

export async function adminDeleteUser(
  _requestingUser: string,
  username: string
): Promise<{ success: boolean; message: string; error?: string }> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/users/${username}`, {
    method: "DELETE",
    headers: auth,
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.error || `API error: ${response.statusText}`);
  }
  return response.json();
}

// ========================
// RECEIVERS API (Connection Owners)
// ========================

export interface Receiver {
  username: string;
  display_name: string;
  email?: string; // Only present on the auth-required GET /receivers/<username> endpoint
}

export interface ReceiversResponse {
  success: boolean;
  receivers: Receiver[];
  total: number;
  error?: string;
}

export interface ReceiverResponse {
  success: boolean;
  receiver: Receiver;
  error?: string;
}

export async function getAllReceivers(): Promise<ReceiversResponse> {
  const response = await fetch(`${API_BASE_URL}/receivers`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getReceiver(username: string): Promise<ReceiverResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/receivers/${username}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...auth,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

// ========================
// SEARCH HISTORY API
// ========================

export interface SearchHistoryItem {
  id: string;
  query: string;
  total_results: number;
  created_at: string;
  status: string;
}

export interface SearchHistoryResponse {
  success: boolean;
  searches: SearchHistoryItem[];
  total: number;
  error?: string;
}

export async function getUserSearches(
  userName: string
): Promise<SearchHistoryResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/users/${userName}/searches`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...auth,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

// ========================
// BOOKMARKS API
// ========================

export interface Bookmark {
  id: string;
  user_name: string;
  linkedin_url: string;
  bookmarked_at: string;
  notes: string | null;
  candidate: CandidateResult;
}

export interface BookmarksResponse {
  success: boolean;
  bookmarks: Bookmark[];
  total: number;
  error?: string;
}

export interface BookmarkStatusResponse {
  success: boolean;
  is_bookmarked: boolean;
  error?: string;
}

export interface BookmarkActionResponse {
  success: boolean;
  message: string;
  bookmark_id?: string;
  error?: string;
}

export async function getUserBookmarks(
  userName: string
): Promise<BookmarksResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/users/${userName}/bookmarks`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...auth,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function addBookmark(
  userName: string,
  data: {
    linkedin_url: string;
    candidate_name?: string;
    candidate_headline?: string;
    notes?: string;
  }
): Promise<BookmarkActionResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/users/${userName}/bookmarks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...auth,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function removeBookmark(
  userName: string,
  linkedinUrl: string
): Promise<BookmarkActionResponse> {
  const auth = await authHeaders();
  const encodedUrl = encodeURIComponent(linkedinUrl);
  const response = await fetch(
    `${API_BASE_URL}/users/${userName}/bookmarks/${encodedUrl}`,
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        ...auth,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function checkBookmark(
  userName: string,
  linkedinUrl: string
): Promise<BookmarkStatusResponse> {
  const encodedUrl = encodeURIComponent(linkedinUrl);
  const response = await fetch(
    `${API_BASE_URL}/users/${userName}/bookmarks/check/${encodedUrl}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

// ========================
// ADMIN API
// ========================

export interface AdminSearchItem {
  id: string;
  query: string;
  total_results: number;
  created_at: string;
  status: string;
  user_name: string;
}

export interface AdminSearchesResponse {
  success: boolean;
  searches: AdminSearchItem[];
  total: number;
  error?: string;
}

export interface AdminCheckResponse {
  success: boolean;
  is_admin: boolean;
}

export async function checkIsAdmin(
  _userName?: string
): Promise<AdminCheckResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/check`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...auth,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getAdminSearches(
  _userName?: string
): Promise<AdminSearchesResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/searches`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...auth,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

// ========================
// CSV UPLOAD API
// ========================

export interface UploadJob {
  id: string;
  filename: string;
  uploaded_by: string;
  connection_owner: string | null;
  status: string;
  current_step: string | null;
  total_urls: number;
  scraped_urls: number;
  transformed_urls: number;
  failed_urls: number;
  failed_urls_list: string[];
  error_message: string | null;
  logs: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface UploadJobsResponse {
  success: boolean;
  jobs: UploadJob[];
  error?: string;
}

export interface UploadJobResponse {
  success: boolean;
  job: UploadJob;
  error?: string;
}

export interface UploadCSVResponse {
  success: boolean;
  job_id: string;
  message: string;
  error?: string;
}

export async function uploadCSV(
  file: File,
  _userName?: string
): Promise<UploadCSVResponse> {
  const auth = await authHeaders();
  const formData = new FormData();
  formData.append("file", file);

  // This is a LONG request (may take 20-30 minutes)
  // No timeout - let Railway handle it
  const response = await fetch(`${API_BASE_URL}/admin/upload-csv`, {
    method: "POST",
    headers: auth, // no Content-Type — let browser set multipart boundary
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || `API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getUploadJobs(_userName?: string): Promise<UploadJobsResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/jobs`, {
    method: "GET",
    headers: { "Content-Type": "application/json", ...auth },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getUploadJobDetails(
  jobId: string,
  _userName?: string
): Promise<UploadJobResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/jobs/${jobId}`, {
    method: "GET",
    headers: { "Content-Type": "application/json", ...auth },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}
