export const API_BASE = '/api';

export async function fetchJson(endpoint: string, options: RequestInit = {}) {
	const res = await fetch(`${API_BASE}${endpoint}`, options);
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
