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
  seniority?: string;
  years_experience?: number;
  skills?: string[];
  connected_to?: string[];
  profile_pic?: string;
  experiences?: Experience[];
  education?: Education[];
  notes?: string;
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
  created_at: string;
  error?: string;
}

export async function searchAndRank(query: string, connectedTo?: string): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/search-and-rank`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      connected_to: connectedTo || 'all'
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
  onProgress: (step: string, message: string) => void
): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/search-and-rank-stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      connected_to: connectedTo || 'all',
      ranking: ranking
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
