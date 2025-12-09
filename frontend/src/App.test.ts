import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App.svelte';
import * as api from './lib/api';

// Mock the api module
vi.mock('./lib/api', () => ({
    fetchJson: vi.fn(),
}));

describe('App Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Mock API calls for Dashboard
        (api.fetchJson as any).mockResolvedValue([]);
    });

    it('renders with Navbar', () => {
        render(App);
        expect(screen.getByText('Receipt Forwarder')).toBeTruthy();
    });

    it('renders Dashboard by default', async () => {
        (api.fetchJson as any)
            .mockResolvedValueOnce({ total_forwarded: 0, total_blocked: 0, total_processed: 0 })
            .mockResolvedValueOnce([]);
            
        render(App);
        
        await waitFor(() => {
            expect(screen.getByText('Total Processed')).toBeTruthy();
        });
    });

    it('switches to Settings view when settings button is clicked', async () => {
        (api.fetchJson as any).mockResolvedValue([]);
        
        render(App);
        
        const settingsButton = screen.getByText('Settings');
        await fireEvent.click(settingsButton);
        
        await waitFor(() => {
            expect(screen.getByText(/Manage your detection rules/i)).toBeTruthy();
        }, { timeout: 3000 });
    });

    it('switches back to Dashboard view when dashboard button is clicked', async () => {
        (api.fetchJson as any).mockResolvedValue([]);
        
        render(App);
        
        // Click settings first
        const settingsButton = screen.getByText('Settings');
        await fireEvent.click(settingsButton);
        
        await waitFor(() => {
            expect(screen.getByText(/Manage your detection rules/i)).toBeTruthy();
        }, { timeout: 3000 });
        
        // Click dashboard to switch back
        const dashboardButton = screen.getByText('Dashboard');
        await fireEvent.click(dashboardButton);
        
        await waitFor(() => {
            expect(screen.getByText('Total Processed')).toBeTruthy();
        }, { timeout: 3000 });
    });

    it('highlights active view in navbar', async () => {
        (api.fetchJson as any).mockResolvedValue([]);
        
        render(App);
        
        const dashboardButton = screen.getByText('Dashboard');
        expect(dashboardButton.closest('button')?.classList.contains('active')).toBe(true);
        
        const settingsButton = screen.getByText('Settings');
        await fireEvent.click(settingsButton);
        
        await waitFor(() => {
            expect(settingsButton.closest('button')?.classList.contains('active')).toBe(true);
        }, { timeout: 3000 });
    });
});
