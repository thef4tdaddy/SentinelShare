import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest';
import { fetchJson, API_BASE, api } from './api';

// Explicitly type the global fetch mock
// const fetchMock = globalThis.fetch as Mock;

describe('API Module', () => {
	beforeEach(() => {
		globalThis.fetch = vi.fn();

		// Mock window.location.search
		const searchParams = new URLSearchParams();
		Object.defineProperty(window, 'location', {
			value: {
				search: searchParams.toString()
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
		expect(globalThis.fetch).toHaveBeenCalledWith(
			'/api/test?token=test-token-123',
			{}
		);
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

		expect(globalThis.fetch).toHaveBeenCalledWith(
			'/api/test?foo=bar&token=stored-token',
			{}
		);
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

		expect(globalThis.fetch).toHaveBeenCalledWith(
			'/api/test?token=stored-token',
			{}
		);
	});
});

describe('API Learning Methods', () => {
	beforeEach(() => {
		globalThis.fetch = vi.fn();

		// Mock window.location.search
		Object.defineProperty(window, 'location', {
			value: {
				search: ''
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
});
