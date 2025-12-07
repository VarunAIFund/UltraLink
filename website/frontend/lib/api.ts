/**
 * API client for Flask backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

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
  match?: 'strong' | 'partial' | 'no_match';
  relevance_score: number;
  fit_description: string;
  ranking_rationale?: string;
  stage_1_confidence?: number;
  score?: number;  // Stage 1 confidence score used for sorting when ranking is off
  seniority?: string;
  years_experience?: number;
  skills?: string[];
  connected_to?: string[];
  profile_pic?: string;
  experiences?: Experience[];
  education?: Education[];
  notes?: string;
  lever_opportunities?: LeverOpportunity[];
  is_bookmarked?: boolean;  // Bookmark status from database JOIN
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

export async function searchAndRank(query: string, connectedTo?: string, userName?: string): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/search-and-rank`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      connected_to: connectedTo || 'all',
      user_name: userName
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
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      connected_to: connectedTo || 'all',
      ranking: ranking,
      user_name: userName
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error('Response body is not readable');
  }

  let buffer = '';
  let finalData: SearchResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE messages (ending with \n\n)
    const messages = buffer.split('\n\n');
    buffer = messages.pop() || ''; // Keep incomplete message in buffer

    for (const message of messages) {
      if (!message.trim()) continue;

      // Parse SSE message (format: "data: {json}")
      const dataMatch = message.match(/^data: (.+)$/m);
      if (dataMatch) {
        try {
          const event = JSON.parse(dataMatch[1]);

          if (event.step === 'complete' && event.data) {
            finalData = event.data;
          } else if (event.step === 'error') {
            throw new Error(event.message);
          } else if (event.step === 'search_created' && event.search_id) {
            // Search ID received - notify callback immediately
            if (onSearchIdReceived) {
              onSearchIdReceived(event.search_id);
            }
          } else {
            // Progress update
            onProgress(event.step, event.message);
          }
        } catch (e) {
          console.error('Failed to parse SSE message:', e);
        }
      }
    }
  }

  if (!finalData) {
    throw new Error('No final data received from server');
  }

  return finalData;
}

export async function generateHighlights(candidate: CandidateResult): Promise<HighlightsResponse> {
  const response = await fetch(`${API_BASE_URL}/generate-highlights`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ candidate }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getSearchSession(searchId: string): Promise<SavedSearchResponse> {
  const response = await fetch(`${API_BASE_URL}/search/${searchId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
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

export async function getNoteForCandidate(linkedinUrl: string): Promise<NoteResponse> {
  const encodedUrl = encodeURIComponent(linkedinUrl);
  const response = await fetch(`${API_BASE_URL}/notes/${encodedUrl}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function updateNoteForCandidate(linkedinUrl: string, note: string): Promise<UpdateNoteResponse> {
  const response = await fetch(`${API_BASE_URL}/notes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      linkedin_url: linkedinUrl,
      note: note
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
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      candidate: candidate,
      job_description: jobDescription,
      mutual_connection_name: mutualConnectionName,
      sender_info: {
        name: senderName || 'Varun Sharma',
        role: 'Partner',
        company: 'AI Fund',
        email: fromEmail
      }
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
  fromEmail: string,
  senderName?: string,
  toEmail?: string
): Promise<SendEmailResponse> {
  const response = await fetch(`${API_BASE_URL}/send-introduction-email`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      to_email: toEmail || 'varun@aifund.ai',
      subject: subject,
      body: body,
      sender_info: {
        name: senderName || 'Varun Sharma',
        email: fromEmail
      }
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
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getUser(userName: string): Promise<UserResponse> {
  const response = await fetch(`${API_BASE_URL}/users/${userName}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
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

export async function getUserSearches(userName: string): Promise<SearchHistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/users/${userName}/searches`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
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

export async function getUserBookmarks(userName: string): Promise<BookmarksResponse> {
  const response = await fetch(`${API_BASE_URL}/users/${userName}/bookmarks`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
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
  const response = await fetch(`${API_BASE_URL}/users/${userName}/bookmarks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function removeBookmark(userName: string, linkedinUrl: string): Promise<BookmarkActionResponse> {
  const encodedUrl = encodeURIComponent(linkedinUrl);
  const response = await fetch(`${API_BASE_URL}/users/${userName}/bookmarks/${encodedUrl}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function checkBookmark(userName: string, linkedinUrl: string): Promise<BookmarkStatusResponse> {
  const encodedUrl = encodeURIComponent(linkedinUrl);
  const response = await fetch(`${API_BASE_URL}/users/${userName}/bookmarks/check/${encodedUrl}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}
