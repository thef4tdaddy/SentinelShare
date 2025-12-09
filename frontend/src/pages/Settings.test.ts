import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import Settings from './Settings.svelte';
import * as api from '../lib/api';

// Mock the api module
vi.mock('../lib/api', () => ({
    fetchJson: vi.fn(),
}));

describe('Settings Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        global.confirm = vi.fn(() => true);
        global.alert = vi.fn();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('renders settings title', () => {
        render(Settings);
        expect(screen.getByText('Settings')).toBeTruthy();
    });

    it('renders description text', () => {
        render(Settings);
        expect(screen.getByText(/Manage your detection rules and preferences/i)).toBeTruthy();
    });

    it('renders Run Now button', () => {
        render(Settings);
        expect(screen.getByText('Run Now')).toBeTruthy();
    });

    it('renders PreferenceList components', async () => {
        (api.fetchJson as any).mockResolvedValue([]);
        
        render(Settings);
        
        await waitFor(() => {
            expect(screen.getByText('Preferences')).toBeTruthy();
            expect(screen.getByText('Manual Rules')).toBeTruthy();
        });
    });

    it('triggers poll when Run Now is clicked and confirmed', async () => {
        const mockResponse = { message: 'Poll triggered successfully' };
        (api.fetchJson as any).mockResolvedValue(mockResponse);
        
        render(Settings);
        
        const runNowButton = screen.getByText('Run Now');
        await fireEvent.click(runNowButton);
        
        await waitFor(() => {
            expect(global.confirm).toHaveBeenCalledWith('Run email check now?');
            expect(api.fetchJson).toHaveBeenCalledWith('/settings/trigger-poll', {
                method: 'POST',
            });
            expect(global.alert).toHaveBeenCalledWith('Poll triggered successfully');
        });
    });

    it('does not trigger poll if user cancels confirmation', async () => {
        global.confirm = vi.fn(() => false);
        (api.fetchJson as any).mockResolvedValue([]);
        
        render(Settings);
        
        await waitFor(() => {
            expect(screen.getByText('Run Now')).toBeTruthy();
        });
        
        // Clear the calls from PreferenceList mount
        vi.clearAllMocks();
        
        const runNowButton = screen.getByText('Run Now');
        await fireEvent.click(runNowButton);
        
        expect(global.confirm).toHaveBeenCalledWith('Run email check now?');
        expect(api.fetchJson).not.toHaveBeenCalled();
    });

    it('shows default message if API response has no message', async () => {
        (api.fetchJson as any).mockResolvedValue({});
        
        render(Settings);
        
        const runNowButton = screen.getByText('Run Now');
        await fireEvent.click(runNowButton);
        
        await waitFor(() => {
            expect(global.alert).toHaveBeenCalledWith('Poll triggered');
        });
    });

    it('handles trigger poll error gracefully', async () => {
        (api.fetchJson as any).mockRejectedValue(new Error('API Error'));
        
        render(Settings);
        
        const runNowButton = screen.getByText('Run Now');
        await fireEvent.click(runNowButton);
        
        await waitFor(() => {
            expect(global.alert).toHaveBeenCalledWith('Error triggering poll');
        });
    });
});
