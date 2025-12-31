import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest';
import { fetchJson, API_BASE, api } from './api';

// Helper function to set up common mocks
function setupMocks(searchQuery = '') {
	globalThis.fetch = vi.fn();

	// Mock window.location.search
	Object.defineProperty(window, 'location', {
		value: {
			search: searchQuery
		},
		writable: true
	});

	// Mock localStorage
	const localStorageMock = (function () {
		let store: Record<string, string> = {};
		return {
			getItem: vi.fn((key: string) => store[key] || null),
			setItem: vi.fn((key: string, value: string) => {
				store[key] = value.toString();
			}),
			clear: vi.fn(() => {
				store = {};
			}),
			removeItem: vi.fn((key: string) => {
				delete store[key];
			})
		};
	})();
	Object.defineProperty(window, 'localStorage', { value: localStorageMock });
}

describe('API Module', () => {
	beforeEach(() => {
		setupMocks();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('exports correct API_BASE', () => {
		expect(API_BASE).toBe('/api');
	});

	it('makes a GET request by default', async () => {
		const mockData = { message: 'success' };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockData
		});

		const result = await fetchJson('/test');

		expect(globalThis.fetch).toHaveBeenCalledWith('/api/test', {});
		expect(result).toEqual(mockData);
	});

	it('makes a POST request with options', async () => {
		const mockData = { id: 1 };
		const requestBody = { name: 'test' };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockData
		});

		const result = await fetchJson('/test', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(requestBody)
		});

		expect(globalThis.fetch).toHaveBeenCalledWith('/api/test', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(requestBody)
		});
		expect(result).toEqual(mockData);
	});

	it('throws error when response is not ok', async () => {
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: false,
			statusText: 'Not Found'
		});

		await expect(fetchJson('/test')).rejects.toThrow('API Error: Not Found');
	});

	it('makes a DELETE request', async () => {
		const mockData = { success: true };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockData
		});

		const result = await fetchJson('/test/1', { method: 'DELETE' });

		expect(globalThis.fetch).toHaveBeenCalledWith('/api/test/1', { method: 'DELETE' });
		expect(result).toEqual(mockData);
	});

	it('handles network errors', async () => {
		(globalThis.fetch as Mock).mockRejectedValueOnce(new Error('Network error'));

		await expect(fetchJson('/test')).rejects.toThrow('Network error');
	});

	it('stores token from URL query params to localStorage', async () => {
		const mockData = { message: 'success' };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockData
		});

		// Set up URL with token
		Object.defineProperty(window, 'location', {
			value: {
				search: '?token=test-token-123'
			},
			writable: true
		});

		await fetchJson('/test');

		expect(window.localStorage.setItem).toHaveBeenCalledWith('dashboard_token', 'test-token-123');
		expect(globalThis.fetch).toHaveBeenCalledWith('/api/test?token=test-token-123', {});
	});

	it('appends token to URL with existing query params', async () => {
		const mockData = { message: 'success' };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockData
		});

		// Set token in localStorage
		window.localStorage.setItem('dashboard_token', 'stored-token');

		await fetchJson('/test?foo=bar');

		expect(globalThis.fetch).toHaveBeenCalledWith('/api/test?foo=bar&token=stored-token', {});
	});

	it('appends token to URL without existing query params', async () => {
		const mockData = { message: 'success' };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockData
		});

		// Set token in localStorage
		window.localStorage.setItem('dashboard_token', 'stored-token');

		await fetchJson('/test');

		expect(globalThis.fetch).toHaveBeenCalledWith('/api/test?token=stored-token', {});
	});

	it('handles SSR scenario when window is undefined', async () => {
		// Save original window
		const originalWindow = globalThis.window;

		// Remove window to simulate SSR
		// @ts-expect-error - Testing SSR scenario
		delete globalThis.window;

		const mockData = { message: 'success' };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockData
		});

		const result = await fetchJson('/test');

		expect(globalThis.fetch).toHaveBeenCalledWith('/api/test', {});
		expect(result).toEqual(mockData);

		// Restore window
		globalThis.window = originalWindow;
	});

	it('handles when window.localStorage is not available', async () => {
		// Save original localStorage descriptor
		const descriptor = Object.getOwnPropertyDescriptor(window, 'localStorage');

		// Remove localStorage to test fallback
		// @ts-expect-error - Testing localStorage unavailable scenario
		Object.defineProperty(window, 'localStorage', {
			value: undefined,
			writable: true,
			configurable: true
		});

		const mockData = { message: 'success' };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockData
		});

		const result = await fetchJson('/test');

		expect(globalThis.fetch).toHaveBeenCalledWith('/api/test', {});
		expect(result).toEqual(mockData);

		// Restore localStorage
		if (descriptor) {
			Object.defineProperty(window, 'localStorage', descriptor);
		}
	});

	it('encodes token in URL properly', async () => {
		const mockData = { message: 'success' };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockData
		});

		// Set token with special characters that need encoding
		window.localStorage.setItem('dashboard_token', 'token+with/special=chars');

		await fetchJson('/test');

		expect(globalThis.fetch).toHaveBeenCalledWith(
			'/api/test?token=token%2Bwith%2Fspecial%3Dchars',
			{}
		);
	});
});

describe('API Learning Methods', () => {
	beforeEach(() => {
		setupMocks();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('api.learning.scan makes POST request with days parameter', async () => {
		const mockResponse = { message: 'Scan initiated' };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockResponse
		});

		const result = await api.learning.scan(7);

		expect(globalThis.fetch).toHaveBeenCalledWith('/api/learning/scan', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ days: 7 })
		});
		expect(result).toEqual(mockResponse);
	});

	it('api.learning.getCandidates makes GET request', async () => {
		const mockCandidates = [
			{
				id: 1,
				sender: 'test@example.com',
				confidence: 0.95,
				type: 'receipt',
				matches: 5,
				created_at: '2024-01-01T00:00:00Z'
			}
		];
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockCandidates
		});

		const result = await api.learning.getCandidates();

		expect(globalThis.fetch).toHaveBeenCalledWith('/api/learning/candidates', {});
		expect(result).toEqual(mockCandidates);
	});

	it('api.learning.approve makes POST request with candidate ID', async () => {
		const mockResponse = { success: true };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockResponse
		});

		const result = await api.learning.approve(42);

		expect(globalThis.fetch).toHaveBeenCalledWith('/api/learning/approve/42', { method: 'POST' });
		expect(result).toEqual(mockResponse);
	});

	it('api.learning.ignore makes DELETE request with candidate ID', async () => {
		const mockResponse = { success: true };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockResponse
		});

		const result = await api.learning.ignore(42);

		expect(globalThis.fetch).toHaveBeenCalledWith('/api/learning/ignore/42', { method: 'DELETE' });
		expect(result).toEqual(mockResponse);
	});

	it('api.learning.scan uses default days parameter when not provided', async () => {
		const mockResponse = { message: 'Scan initiated' };
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockResponse
		});

		const result = await api.learning.scan();

		expect(globalThis.fetch).toHaveBeenCalledWith('/api/learning/scan', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ days: 30 })
		});
		expect(result).toEqual(mockResponse);
	});

	it('api.learning.scan handles API errors', async () => {
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: false,
			statusText: 'Internal Server Error'
		});

		await expect(api.learning.scan(7)).rejects.toThrow('API Error: Internal Server Error');
	});

	it('api.learning.getCandidates handles API errors', async () => {
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: false,
			statusText: 'Unauthorized'
		});

		await expect(api.learning.getCandidates()).rejects.toThrow('API Error: Unauthorized');
	});

	it('api.learning.approve handles API errors', async () => {
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: false,
			statusText: 'Not Found'
		});

		await expect(api.learning.approve(999)).rejects.toThrow('API Error: Not Found');
	});

	it('api.learning.ignore handles API errors', async () => {
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: false,
			statusText: 'Forbidden'
		});

		await expect(api.learning.ignore(999)).rejects.toThrow('API Error: Forbidden');
	});

	it('api.learning.getCandidates returns proper typed response', async () => {
		const mockCandidates = [
			{
				id: 1,
				sender: 'test@example.com',
				subject_pattern: 'Receipt from.*',
				confidence: 0.95,
				type: 'receipt',
				matches: 5,
				example_subject: 'Receipt from Store',
				created_at: '2024-01-01T00:00:00Z'
			},
			{
				id: 2,
				sender: 'invoice@company.com',
				confidence: 0.85,
				type: 'invoice',
				matches: 3,
				created_at: '2024-01-02T00:00:00Z'
			}
		];
		(globalThis.fetch as Mock).mockResolvedValueOnce({
			ok: true,
			json: async () => mockCandidates
		});

		const result = await api.learning.getCandidates();

		expect(result).toHaveLength(2);
		expect(result[0]).toHaveProperty('id', 1);
		expect(result[0]).toHaveProperty('sender', 'test@example.com');
		expect(result[0]).toHaveProperty('confidence', 0.95);
		expect(result[1]).toHaveProperty('id', 2);
		expect(result[1]).not.toHaveProperty('subject_pattern');
	});
});
