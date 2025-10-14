/**
 * API client for Flask backend
 */

const API_BASE_URL = 'http://localhost:5000';

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
}

export interface SearchResponse {
  success: boolean;
  sql: string;
  results: CandidateResult[];
  total: number;
  error?: string;
}

export async function searchAndRank(query: string): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/search-and-rank`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function healthCheck(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return response.json();
}
