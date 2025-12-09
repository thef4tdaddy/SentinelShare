import { render, screen, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import Dashboard from './Dashboard.svelte';
import * as api from '../lib/api';

// Mock the api module
vi.mock('../lib/api', () => ({
    fetchJson: vi.fn(),
}));

describe('Dashboard Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('renders stats cards', async () => {
        const mockStats = {
            total_forwarded: 10,
            total_blocked: 5,
            total_processed: 15,
        };
        const mockActivity = [];

        (api.fetchJson as any)
            .mockResolvedValueOnce(mockStats)
            .mockResolvedValueOnce(mockActivity);

        render(Dashboard);

        await waitFor(() => {
            expect(screen.getByText('Total Processed')).toBeTruthy();
            expect(screen.getByText('Forwarded')).toBeTruthy();
            expect(screen.getByText('Blocked/Ignored')).toBeTruthy();
        });
    });

    it('displays correct stats values', async () => {
        const mockStats = {
            total_forwarded: 42,
            total_blocked: 13,
            total_processed: 55,
        };
        const mockActivity = [];

        (api.fetchJson as any)
            .mockResolvedValueOnce(mockStats)
            .mockResolvedValueOnce(mockActivity);

        render(Dashboard);

        await waitFor(() => {
            expect(screen.getByText('55')).toBeTruthy();
            expect(screen.getByText('42')).toBeTruthy();
            expect(screen.getByText('13')).toBeTruthy();
        });
    });

    it('renders activity feed', async () => {
        const mockStats = {
            total_forwarded: 0,
            total_blocked: 0,
            total_processed: 0,
        };
        const mockActivity = [
            {
                id: 1,
                subject: 'Test Receipt',
                sender: 'amazon',
                status: 'forwarded',
                category: 'amazon',
                processed_at: new Date().toISOString(),
            },
        ];

        (api.fetchJson as any)
            .mockResolvedValueOnce(mockStats)
            .mockResolvedValueOnce(mockActivity);

        render(Dashboard);

        await waitFor(() => {
            expect(screen.getByText('Recent Activity')).toBeTruthy();
            expect(screen.getByText('Test Receipt')).toBeTruthy();
        });
    });

    it('handles empty activity', async () => {
        const mockStats = {
            total_forwarded: 0,
            total_blocked: 0,
            total_processed: 0,
        };
        const mockActivity = [];

        (api.fetchJson as any)
            .mockResolvedValueOnce(mockStats)
            .mockResolvedValueOnce(mockActivity);

        render(Dashboard);

        await waitFor(() => {
            expect(screen.getByText('No activity found.')).toBeTruthy();
        });
    });

    it('calls correct API endpoints on mount', async () => {
        const mockStats = {
            total_forwarded: 0,
            total_blocked: 0,
            total_processed: 0,
        };
        const mockActivity = [];

        (api.fetchJson as any)
            .mockResolvedValueOnce(mockStats)
            .mockResolvedValueOnce(mockActivity);

        render(Dashboard);

        await waitFor(() => {
            expect(api.fetchJson).toHaveBeenCalledWith('/dashboard/stats');
            expect(api.fetchJson).toHaveBeenCalledWith('/dashboard/activity');
        });
    });

    it('handles API errors gracefully', async () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        
        (api.fetchJson as any).mockRejectedValueOnce(new Error('API Error'));

        render(Dashboard);

        await waitFor(() => {
            expect(consoleSpy).toHaveBeenCalledWith(
                'Failed to load dashboard data',
                expect.any(Error)
            );
        });

        consoleSpy.mockRestore();
    });

    it('displays stats with subtexts', async () => {
        const mockStats = {
            total_forwarded: 10,
            total_blocked: 5,
            total_processed: 15,
        };
        const mockActivity = [];

        (api.fetchJson as any)
            .mockResolvedValueOnce(mockStats)
            .mockResolvedValueOnce(mockActivity);

        render(Dashboard);

        await waitFor(() => {
            expect(screen.getByText('Receipts found')).toBeTruthy();
            expect(screen.getByText('Not receipts')).toBeTruthy();
        });
    });
});
