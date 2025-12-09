import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import PreferenceList from './PreferenceList.svelte';
import * as api from '../lib/api';

// Mock the api module
vi.mock('../lib/api', () => ({
    fetchJson: vi.fn(),
}));

describe('PreferenceList Component - Preferences Type', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Mock window.confirm
        global.confirm = vi.fn(() => true);
        // Mock window.alert
        global.alert = vi.fn();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('renders preferences title', async () => {
        (api.fetchJson as any).mockResolvedValueOnce([]);
        render(PreferenceList, { type: 'preferences' });
        await waitFor(() => {
            expect(screen.getByText('Preferences')).toBeTruthy();
        });
    });

    it('loads and displays preferences on mount', async () => {
        const mockPreferences = [
            { id: 1, item: 'amazon', type: 'Always Forward' },
            { id: 2, item: 'spam', type: 'Blocked Sender' },
        ];
        (api.fetchJson as any).mockResolvedValueOnce(mockPreferences);

        render(PreferenceList, { type: 'preferences' });

        await waitFor(() => {
            expect(screen.getByText('amazon')).toBeTruthy();
            expect(screen.getByText('spam')).toBeTruthy();
        });
    });

    it('renders form fields for preferences', async () => {
        (api.fetchJson as any).mockResolvedValueOnce([]);
        render(PreferenceList, { type: 'preferences' });

        await waitFor(() => {
            expect(screen.getByLabelText(/Item \(e.g., amazon\)/i)).toBeTruthy();
            expect(screen.getByLabelText(/Type/i)).toBeTruthy();
        });
    });

    it('adds a new preference item', async () => {
        const mockNewItem = { id: 3, item: 'ebay', type: 'Always Forward' };
        (api.fetchJson as any).mockResolvedValueOnce([]);
        (api.fetchJson as any).mockResolvedValueOnce(mockNewItem);

        render(PreferenceList, { type: 'preferences' });

        await waitFor(() => {
            expect(screen.getByLabelText(/Item \(e.g., amazon\)/i)).toBeTruthy();
        });

        const itemInput = screen.getByLabelText(/Item \(e.g., amazon\)/i) as HTMLInputElement;
        const typeSelect = screen.getByLabelText(/Type/i) as HTMLSelectElement;
        const addButton = screen.getByText('Add');

        await fireEvent.input(itemInput, { target: { value: 'ebay' } });
        await fireEvent.change(typeSelect, { target: { value: 'Always Forward' } });
        await fireEvent.click(addButton);

        await waitFor(() => {
            // Check that the second call (after mount) was a POST
            const calls = (api.fetchJson as any).mock.calls;
            const postCall = calls.find((call: any) => call[1]?.method === 'POST');
            expect(postCall).toBeDefined();
            expect(postCall[0]).toBe('/settings/preferences');
            expect(postCall[1].method).toBe('POST');
            expect(postCall[1].headers).toEqual({ 'Content-Type': 'application/json' });
            
            // Check that body contains the correct data (order-independent)
            const bodyData = JSON.parse(postCall[1].body);
            expect(bodyData.item).toBe('ebay');
            expect(bodyData.type).toBe('Always Forward');
        });
    });

    it('deletes a preference item', async () => {
        const mockPreferences = [
            { id: 1, item: 'amazon', type: 'Always Forward' },
        ];
        (api.fetchJson as any).mockResolvedValueOnce(mockPreferences);
        (api.fetchJson as any).mockResolvedValueOnce({});

        render(PreferenceList, { type: 'preferences' });

        await waitFor(() => {
            expect(screen.getByText('amazon')).toBeTruthy();
        });

        const deleteButton = screen.getByText('Delete');
        await fireEvent.click(deleteButton);

        await waitFor(() => {
            expect(api.fetchJson).toHaveBeenCalledWith('/settings/preferences/1', {
                method: 'DELETE',
            });
        });
    });

    it('does not delete if user cancels confirmation', async () => {
        global.confirm = vi.fn(() => false);
        const mockPreferences = [
            { id: 1, item: 'amazon', type: 'Always Forward' },
        ];
        (api.fetchJson as any).mockResolvedValueOnce(mockPreferences);

        render(PreferenceList, { type: 'preferences' });

        await waitFor(() => {
            expect(screen.getByText('amazon')).toBeTruthy();
        });

        const deleteButton = screen.getByText('Delete');
        await fireEvent.click(deleteButton);

        // fetchJson should only be called once (for loading)
        expect(api.fetchJson).toHaveBeenCalledTimes(1);
    });

    it('handles add error gracefully', async () => {
        (api.fetchJson as any).mockResolvedValueOnce([]);
        (api.fetchJson as any).mockRejectedValueOnce(new Error('API Error'));

        render(PreferenceList, { type: 'preferences' });

        await waitFor(() => {
            expect(screen.getByText('Add')).toBeTruthy();
        });

        const addButton = screen.getByText('Add');
        await fireEvent.click(addButton);

        await waitFor(() => {
            expect(global.alert).toHaveBeenCalledWith('Error adding item');
        });
    });

    it('handles delete error gracefully', async () => {
        const mockPreferences = [
            { id: 1, item: 'amazon', type: 'Always Forward' },
        ];
        (api.fetchJson as any).mockResolvedValueOnce(mockPreferences);
        (api.fetchJson as any).mockRejectedValueOnce(new Error('API Error'));

        render(PreferenceList, { type: 'preferences' });

        await waitFor(() => {
            expect(screen.getByText('amazon')).toBeTruthy();
        });

        const deleteButton = screen.getByText('Delete');
        await fireEvent.click(deleteButton);

        await waitFor(() => {
            expect(global.alert).toHaveBeenCalledWith('Error deleting item');
        });
    });
});

describe('PreferenceList Component - Rules Type', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        global.confirm = vi.fn(() => true);
        global.alert = vi.fn();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('renders rules title', async () => {
        (api.fetchJson as any).mockResolvedValueOnce([]);
        render(PreferenceList, { type: 'rules' });
        await waitFor(() => {
            expect(screen.getByText('Manual Rules')).toBeTruthy();
        });
    });

    it('renders form fields for rules', async () => {
        (api.fetchJson as any).mockResolvedValueOnce([]);
        render(PreferenceList, { type: 'rules' });

        await waitFor(() => {
            expect(screen.getByLabelText(/Email Pattern/i)).toBeTruthy();
            expect(screen.getByLabelText(/Subject Pattern/i)).toBeTruthy();
            expect(screen.getByLabelText(/Purpose/i)).toBeTruthy();
        });
    });

    it('loads and displays rules on mount', async () => {
        const mockRules = [
            { id: 1, email_pattern: '@amazon.com', subject_pattern: 'order', purpose: 'Amazon orders' },
            { id: 2, email_pattern: '@ebay.com', subject_pattern: 'purchase', purpose: 'eBay purchases' },
        ];
        (api.fetchJson as any).mockResolvedValueOnce(mockRules);

        render(PreferenceList, { type: 'rules' });

        await waitFor(() => {
            expect(screen.getByText('@amazon.com')).toBeTruthy();
            expect(screen.getByText('@ebay.com')).toBeTruthy();
        });
    });

    it('handles missing field values with dash', async () => {
        const mockRules = [
            { id: 1, email_pattern: '@amazon.com', subject_pattern: '', purpose: '' },
        ];
        (api.fetchJson as any).mockResolvedValueOnce(mockRules);

        render(PreferenceList, { type: 'rules' });

        await waitFor(() => {
            expect(screen.getByText('@amazon.com')).toBeTruthy();
            const dashes = screen.getAllByText('-');
            expect(dashes.length).toBeGreaterThan(0);
        });
    });
});
