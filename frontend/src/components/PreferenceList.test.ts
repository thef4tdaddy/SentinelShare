import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import PreferenceList from './PreferenceList.svelte';
import * as api from '../lib/api';

// Mock the api module
vi.mock('../lib/api', () => ({
	fetchJson: vi.fn()
}));

describe('PreferenceList Component - Preferences Type', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		// Mock window.alert
		window.alert = vi.fn();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('renders preferences title', async () => {
		vi.mocked(api.fetchJson).mockResolvedValueOnce([]);
		render(PreferenceList, { type: 'preferences' });
		await waitFor(() => {
			expect(screen.getByText('Add New Preference')).toBeTruthy();
		});
	});

	it('loads and displays preferences on mount', async () => {
		const mockPreferences = [
			{ id: 1, item: 'amazon', type: 'Always Forward' },
			{ id: 2, item: 'spam', type: 'Blocked Sender' }
		];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(PreferenceList, { type: 'preferences' });

		await waitFor(() => {
			expect(screen.getByText('amazon')).toBeTruthy();
			expect(screen.getByText('spam')).toBeTruthy();
		});
	});

	it('renders form fields for preferences', async () => {
		vi.mocked(api.fetchJson).mockResolvedValueOnce([]);
		render(PreferenceList, { type: 'preferences' });

		await waitFor(() => {
			expect(screen.getByLabelText(/Item \(e.g., amazon\)/i)).toBeTruthy();
			expect(screen.getByLabelText(/Type/i)).toBeTruthy();
		});
	});

	it('adds a new preference item', async () => {
		const mockNewItem = { id: 3, item: 'ebay', type: 'Always Forward' };
		vi.mocked(api.fetchJson).mockResolvedValueOnce([]);
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockNewItem);

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
			const calls = vi.mocked(api.fetchJson).mock.calls;
			const postCall = calls.find((call) => call[1]?.method === 'POST');

			expect(postCall).toBeDefined();
			if (!postCall || !postCall[1]) throw new Error('No POST call found');

			expect(postCall[0]).toBe('/settings/preferences');
			expect(postCall[1].method).toBe('POST');
			expect(postCall[1].headers).toEqual({ 'Content-Type': 'application/json' });

			// Check that body contains the correct data (order-independent)
			const bodyData = JSON.parse(postCall[1].body as string);
			expect(bodyData.item).toBe('ebay');
			expect(bodyData.type).toBe('Always Forward');
		});
	});

	it('deletes a preference item', async () => {
		const mockPreferences = [{ id: 1, item: 'amazon', type: 'Always Forward' }];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);
		vi.mocked(api.fetchJson).mockResolvedValueOnce({});

		render(PreferenceList, { type: 'preferences' });

		await waitFor(() => {
			expect(screen.getByText('amazon')).toBeTruthy();
		});

		const deleteButton = screen.getByTitle('Delete');
		await fireEvent.click(deleteButton);

		// Modal should open
		await waitFor(() => {
			expect(screen.getByText('Confirm Delete')).toBeTruthy();
		});

		// Click confirm button (look for button with class btn-danger)
		const buttons = screen.getAllByRole('button');
		const confirmButton = buttons.find((btn) => btn.classList.contains('btn-danger'));
		if (!confirmButton) throw new Error('Confirm button not found');
		await fireEvent.click(confirmButton);

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith('/settings/preferences/1', {
				method: 'DELETE'
			});
		});
	});

	it('does not delete if user cancels confirmation', async () => {
		const mockPreferences = [{ id: 1, item: 'amazon', type: 'Always Forward' }];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(PreferenceList, { type: 'preferences' });

		await waitFor(() => {
			expect(screen.getByText('amazon')).toBeTruthy();
		});

		const deleteButton = screen.getByTitle('Delete');
		await fireEvent.click(deleteButton);

		// Modal should open
		await waitFor(() => {
			expect(screen.getByText('Confirm Delete')).toBeTruthy();
		});

		// Click cancel button (look for button with class btn-secondary)
		const buttons = screen.getAllByRole('button');
		const cancelButton = buttons.find((btn) => btn.classList.contains('btn-secondary'));
		if (!cancelButton) throw new Error('Cancel button not found');
		await fireEvent.click(cancelButton);

		// fetchJson should only be called once (for loading)
		expect(api.fetchJson).toHaveBeenCalledTimes(1);
	});

	it('handles add error gracefully', async () => {
		vi.mocked(api.fetchJson).mockResolvedValueOnce([]);
		vi.mocked(api.fetchJson).mockRejectedValueOnce(new Error('API Error'));

		render(PreferenceList, { type: 'preferences' });

		await waitFor(() => {
			expect(screen.getByText('Add')).toBeTruthy();
		});

		const addButton = screen.getByText('Add');
		await fireEvent.click(addButton);

		await waitFor(() => {
			expect(window.alert).toHaveBeenCalledWith('Error adding item');
		});
	});

	it('handles delete error gracefully', async () => {
		const mockPreferences = [{ id: 1, item: 'amazon', type: 'Always Forward' }];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);
		vi.mocked(api.fetchJson).mockRejectedValueOnce(new Error('API Error'));

		render(PreferenceList, { type: 'preferences' });

		await waitFor(() => {
			expect(screen.getByText('amazon')).toBeTruthy();
		});

		const deleteButton = screen.getByTitle('Delete');
		await fireEvent.click(deleteButton);

		// Modal should open
		await waitFor(() => {
			expect(screen.getByText('Confirm Delete')).toBeTruthy();
		});

		// Click confirm button (look for button with class btn-danger)
		const buttons = screen.getAllByRole('button');
		const confirmButton = buttons.find((btn) => btn.classList.contains('btn-danger'));
		if (!confirmButton) throw new Error('Confirm button not found');
		await fireEvent.click(confirmButton);

		await waitFor(() => {
			expect(window.alert).toHaveBeenCalledWith('Error deleting item');
		});
	});
});

describe('PreferenceList Component - Rules Type', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		window.alert = vi.fn();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('renders rules title', async () => {
		vi.mocked(api.fetchJson).mockResolvedValueOnce([]);
		render(PreferenceList, { type: 'rules' });
		await waitFor(() => {
			expect(screen.getByText('Add New Rule')).toBeTruthy();
		});
	});

	it('renders form fields for rules', async () => {
		vi.mocked(api.fetchJson).mockResolvedValueOnce([]);
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
			{ id: 2, email_pattern: '@ebay.com', subject_pattern: 'purchase', purpose: 'eBay purchases' }
		];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockRules);

		render(PreferenceList, { type: 'rules' });

		await waitFor(() => {
			expect(screen.getByText('@amazon.com')).toBeTruthy();
			expect(screen.getByText('@ebay.com')).toBeTruthy();
		});
	});

	it('handles missing field values with dash', async () => {
		const mockRules = [{ id: 1, email_pattern: '@amazon.com', subject_pattern: '', purpose: '' }];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockRules);

		render(PreferenceList, { type: 'rules' });

		await waitFor(() => {
			expect(screen.getByText('@amazon.com')).toBeTruthy();
			const dashes = screen.getAllByText('-');
			expect(dashes.length).toBeGreaterThan(0);
		});
	});
});
