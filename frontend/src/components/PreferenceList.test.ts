import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import PreferenceList from './PreferenceList.svelte';
import * as api from '../lib/api';
import { toasts } from '../lib/stores/toast';

// Mock the api module
vi.mock('../lib/api', () => ({
	fetchJson: vi.fn()
}));

vi.mock('../lib/stores/toast', () => ({
	toasts: {
		trigger: vi.fn(),
		subscribe: vi.fn(() => () => {}),
		remove: vi.fn()
	}
}));

describe('PreferenceList Component - Preferences Type', () => {
	beforeEach(() => {
		vi.clearAllMocks();
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
			expect(screen.getAllByText('amazon').length).toBeGreaterThanOrEqual(1);
			expect(screen.getAllByText('spam').length).toBeGreaterThanOrEqual(1);
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
			expect(screen.getAllByText('amazon').length).toBeGreaterThanOrEqual(1);
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
			expect(screen.getAllByText('amazon').length).toBeGreaterThanOrEqual(1);
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
			expect(toasts.trigger).toHaveBeenCalledWith('Error adding item', 'error');
		});
	});

	it('handles delete error gracefully', async () => {
		const mockPreferences = [{ id: 1, item: 'amazon', type: 'Always Forward' }];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);
		vi.mocked(api.fetchJson).mockRejectedValueOnce(new Error('API Error'));

		render(PreferenceList, { type: 'preferences' });

		await waitFor(() => {
			expect(screen.getAllByText('amazon').length).toBeGreaterThanOrEqual(1);
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
			expect(toasts.trigger).toHaveBeenCalledWith('Error deleting item', 'error');
		});
	});

	it('handles load error gracefully and logs to console', async () => {
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
		vi.mocked(api.fetchJson).mockRejectedValueOnce(new Error('API Error'));

		render(PreferenceList, { type: 'preferences' });

		await waitFor(() => {
			expect(consoleErrorSpy).toHaveBeenCalledWith('Error loading items');
		});

		consoleErrorSpy.mockRestore();
	});

	it('deletes a preference item from mobile view', async () => {
		const mockPreferences = [{ id: 1, item: 'amazon', type: 'Always Forward' }];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);
		vi.mocked(api.fetchJson).mockResolvedValueOnce({});

		render(PreferenceList, { type: 'preferences' });

		await waitFor(() => {
			expect(screen.getAllByText('amazon').length).toBeGreaterThanOrEqual(1);
		});

		// Find delete button by aria-label for mobile view
		const deleteButtons = screen.getAllByLabelText('Delete');
		// Assume the first delete button corresponds to the mobile view
		const mobileDeleteButton = deleteButtons[0];
		if (!mobileDeleteButton) throw new Error('Delete button not found');
		await fireEvent.click(mobileDeleteButton);

		// Modal should open
		await waitFor(() => {
			expect(screen.getByText('Confirm Delete')).toBeTruthy();
		});

		// Click confirm button
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

	it('renders ConfirmDialog with correct props', async () => {
		const mockPreferences = [{ id: 1, item: 'amazon', type: 'Always Forward' }];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		const { container } = render(PreferenceList, { type: 'preferences' });

		await waitFor(() => {
			expect(screen.getAllByText('amazon').length).toBeGreaterThanOrEqual(1);
		});

		const deleteButton = screen.getByTitle('Delete');
		await fireEvent.click(deleteButton);

		// Modal should open with correct message for preferences
		await waitFor(() => {
			expect(screen.getByText('Confirm Delete')).toBeTruthy();
			expect(
				screen.getByText(/Are you sure you want to delete this preference/i)
			).toBeTruthy();
		});

		// Cancel and verify dialog closes (tests the bind:isOpen)
		const buttons = screen.getAllByRole('button');
		const cancelButton = buttons.find((btn) => btn.classList.contains('btn-secondary'));
		if (!cancelButton) throw new Error('Cancel button not found');
		await fireEvent.click(cancelButton);

		// Dialog should close
		await waitFor(() => {
			expect(screen.queryByText('Confirm Delete')).toBeFalsy();
		});
	});
});

describe('PreferenceList Component - Rules Type', () => {
	beforeEach(() => {
		vi.clearAllMocks();
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
			expect(screen.getAllByText('@amazon.com').length).toBeGreaterThanOrEqual(1);
			expect(screen.getAllByText('@ebay.com').length).toBeGreaterThanOrEqual(1);
		});
	});

	it('handles missing field values with dash', async () => {
		const mockRules = [{ id: 1, email_pattern: '@amazon.com', subject_pattern: '', purpose: '' }];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockRules);

		render(PreferenceList, { type: 'rules' });

		await waitFor(() => {
			expect(screen.getAllByText('@amazon.com').length).toBeGreaterThanOrEqual(1);
			const dashes = screen.getAllByText('-');
			expect(dashes.length).toBeGreaterThan(0);
		});
	});

	it('renders ConfirmDialog with correct props for rules', async () => {
		const mockRules = [
			{ id: 1, email_pattern: '@amazon.com', subject_pattern: 'order', purpose: 'Amazon orders' }
		];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockRules);

		render(PreferenceList, { type: 'rules' });

		await waitFor(() => {
			expect(screen.getAllByText('@amazon.com').length).toBeGreaterThanOrEqual(1);
		});

		const deleteButton = screen.getByTitle('Delete');
		await fireEvent.click(deleteButton);

		// Modal should open with correct message for rules
		await waitFor(() => {
			expect(screen.getByText('Confirm Delete')).toBeTruthy();
			expect(screen.getByText(/Are you sure you want to delete this rule/i)).toBeTruthy();
		});
	});

	it('closes dialog with Escape key', async () => {
		const mockRules = [
			{ id: 1, email_pattern: '@amazon.com', subject_pattern: 'order', purpose: 'Amazon orders' }
		];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockRules);

		render(PreferenceList, { type: 'rules' });

		await waitFor(() => {
			expect(screen.getAllByText('@amazon.com').length).toBeGreaterThanOrEqual(1);
		});

		const deleteButton = screen.getByTitle('Delete');
		await fireEvent.click(deleteButton);

		// Modal should open
		await waitFor(() => {
			expect(screen.getByText('Confirm Delete')).toBeTruthy();
		});

		// Press Escape to close
		await fireEvent.keyDown(document.body, { key: 'Escape' });

		// Dialog should close via the binding
		await waitFor(() => {
			expect(screen.queryByText('Confirm Delete')).toBeFalsy();
		});
	});
});
