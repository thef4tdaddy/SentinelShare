import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { fetchJson, API_BASE } from './api';

describe('API Module', () => {
    beforeEach(() => {
        global.fetch = vi.fn();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('exports correct API_BASE', () => {
        expect(API_BASE).toBe('/api');
    });

    it('makes a GET request by default', async () => {
        const mockData = { message: 'success' };
        (global.fetch as any).mockResolvedValueOnce({
            ok: true,
            json: async () => mockData,
        });

        const result = await fetchJson('/test');
        
        expect(global.fetch).toHaveBeenCalledWith('/api/test', {});
        expect(result).toEqual(mockData);
    });

    it('makes a POST request with options', async () => {
        const mockData = { id: 1 };
        const requestBody = { name: 'test' };
        (global.fetch as any).mockResolvedValueOnce({
            ok: true,
            json: async () => mockData,
        });

        const result = await fetchJson('/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
        });

        expect(global.fetch).toHaveBeenCalledWith('/api/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
        });
        expect(result).toEqual(mockData);
    });

    it('throws error when response is not ok', async () => {
        (global.fetch as any).mockResolvedValueOnce({
            ok: false,
            statusText: 'Not Found',
        });

        await expect(fetchJson('/test')).rejects.toThrow('API Error: Not Found');
    });

    it('makes a DELETE request', async () => {
        const mockData = { success: true };
        (global.fetch as any).mockResolvedValueOnce({
            ok: true,
            json: async () => mockData,
        });

        const result = await fetchJson('/test/1', { method: 'DELETE' });

        expect(global.fetch).toHaveBeenCalledWith('/api/test/1', { method: 'DELETE' });
        expect(result).toEqual(mockData);
    });

    it('handles network errors', async () => {
        (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

        await expect(fetchJson('/test')).rejects.toThrow('Network error');
    });
});
