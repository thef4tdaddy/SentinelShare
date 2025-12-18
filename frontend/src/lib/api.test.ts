import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest';
import { fetchJson, API_BASE } from './api';

// Explicitly type the global fetch mock
// const fetchMock = globalThis.fetch as Mock;

describe('API Module', () => {
	beforeEach(() => {
		globalThis.fetch = vi.fn();
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
});
