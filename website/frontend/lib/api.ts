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
  relevance_score: number;
  fit_description: string;
  seniority?: string;
  years_experience?: number;
  skills?: string[];
  connected_to?: string[];
  profile_pic?: string;
  experiences?: Experience[];
  education?: Education[];
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
