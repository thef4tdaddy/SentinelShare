export const API_BASE = '/api';

export async function fetchJson(endpoint: string, options: RequestInit = {}) {
	// Check for token in URL query params or localStorage
	let token: string | null = null;
	if (typeof window !== 'undefined' && window.localStorage) {
		const searchParams = new URLSearchParams(window.location.search);
		token = searchParams.get('token');
		if (token) {
			localStorage.setItem('dashboard_token', token);
		} else {
			token = localStorage.getItem('dashboard_token');
		}
	}

	let url = `${API_BASE}${endpoint}`;
	if (token) {
		// Append token
		const separator = url.includes('?') ? '&' : '?';
		url += `${separator}token=${encodeURIComponent(token)}`;
	}

	const res = await fetch(url, options);
	if (!res.ok) {
		throw new Error(`API Error: ${res.statusText}`);
	}
	return res.json();
}

export interface LearningCandidate {
	id: number;
	sender: string;
	subject_pattern?: string;
	confidence: number;
	type: string;
	matches: number;
	example_subject?: string;
	created_at: string;
}

export const api = {
	learning: {
		scan: async (days = 30) => {
			return fetchJson('/learning/scan', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ days })
			});
		},
		getCandidates: async (): Promise<LearningCandidate[]> => {
			return fetchJson('/learning/candidates');
		},
		approve: async (candidateId: number) => {
			return fetchJson(`/learning/approve/${candidateId}`, { method: 'POST' });
		},
		ignore: async (candidateId: number) => {
			return fetchJson(`/learning/ignore/${candidateId}`, { method: 'DELETE' });
		}
	}
};
