import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import Settings from './Settings.svelte';
import * as api from '../lib/api';

// Mock the api module
vi.mock('../lib/api', () => ({
	fetchJson: vi.fn()
}));

describe('Settings Component', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		window.alert = vi.fn();
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
		expect(screen.getByText(/Manage detection rules and preferences/i)).toBeTruthy();
	});

	it('renders Run Now button', () => {
		render(Settings);
		expect(screen.getByText('Run Now')).toBeTruthy();
	});

	it('renders PreferenceList components', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Add New Preference')).toBeTruthy();
			expect(screen.getByText('Add New Rule')).toBeTruthy();
		});
	});

	it('triggers poll when Run Now is clicked and confirmed', async () => {
		const mockResponse = { message: 'Poll triggered successfully' };
		// Mock all API calls that happen on mount
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce([]) // PreferenceList preferences
			.mockResolvedValueOnce([]) // PreferenceList rules
			.mockResolvedValueOnce({ template: '' }) // EmailTemplateEditor
			.mockResolvedValueOnce([]); // checkConnections

		render(Settings);

		const runNowButton = screen.getByText('Run Now');
		await fireEvent.click(runNowButton);

		// Modal should open
		await waitFor(() => {
			expect(screen.getByText('Run Email Check')).toBeTruthy();
			expect(
				screen.getByText(/Do you want to run the email check now\? This will process all emails/i)
			).toBeTruthy();
		});

		// Click confirm button in modal (the second "Run Now" button)
		const buttons = screen.getAllByRole('button', { name: 'Run Now' });
		const confirmButton = buttons[1]; // The modal button is the second one

		// Mock the trigger-poll response
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockResponse);

		await fireEvent.click(confirmButton);

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith('/settings/trigger-poll', {
				method: 'POST'
			});
			expect(window.alert).toHaveBeenCalledWith('Poll triggered successfully');
		});
	});

	it('does not trigger poll if user cancels confirmation', async () => {
		// Mock all API calls that happen on mount
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce([]) // PreferenceList preferences
			.mockResolvedValueOnce([]) // PreferenceList rules
			.mockResolvedValueOnce({ template: '' }) // EmailTemplateEditor
			.mockResolvedValueOnce([]); // checkConnections

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Run Now')).toBeTruthy();
		});

		// Clear the calls from mount
		vi.clearAllMocks();

		const runNowButton = screen.getByText('Run Now');
		await fireEvent.click(runNowButton);

		// Modal should open
		await waitFor(() => {
			expect(screen.getByText('Run Email Check')).toBeTruthy();
		});

		// Click cancel button
		const cancelButton = screen.getByRole('button', { name: 'Cancel' });
		await fireEvent.click(cancelButton);

		// API should not be called
		expect(api.fetchJson).not.toHaveBeenCalled();
	});

	it('shows default message if API response has no message', async () => {
		// Mock all API calls that happen on mount
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce([]) // PreferenceList preferences
			.mockResolvedValueOnce([]) // PreferenceList rules
			.mockResolvedValueOnce({ template: '' }) // EmailTemplateEditor
			.mockResolvedValueOnce([]); // checkConnections

		render(Settings);

		const runNowButton = screen.getByText('Run Now');
		await fireEvent.click(runNowButton);

		// Modal should open
		await waitFor(() => {
			expect(screen.getByText('Run Email Check')).toBeTruthy();
		});

		// Click confirm button in modal (the second "Run Now" button)
		const buttons = screen.getAllByRole('button', { name: 'Run Now' });
		const confirmButton = buttons[1]; // The modal button is the second one

		// Mock the trigger-poll response with no message
		vi.mocked(api.fetchJson).mockResolvedValueOnce({});

		await fireEvent.click(confirmButton);

		await waitFor(() => {
			expect(window.alert).toHaveBeenCalledWith('Poll triggered');
		});
	});

	it('handles trigger poll error gracefully', async () => {
		// Mock all API calls that happen on mount
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce([]) // PreferenceList preferences
			.mockResolvedValueOnce([]) // PreferenceList rules
			.mockResolvedValueOnce({ template: '' }) // EmailTemplateEditor
			.mockResolvedValueOnce([]); // checkConnections

		render(Settings);

		const runNowButton = screen.getByText('Run Now');
		await fireEvent.click(runNowButton);

		// Modal should open
		await waitFor(() => {
			expect(screen.getByText('Run Email Check')).toBeTruthy();
		});

		// Click confirm button in modal (the second "Run Now" button)
		const buttons = screen.getAllByRole('button', { name: 'Run Now' });
		const confirmButton = buttons[1]; // The modal button is the second one

		// Mock the trigger-poll API error - use mockRejectedValue to ensure it catches even if prior calls exhausted the chain
		vi.mocked(api.fetchJson).mockRejectedValue(new Error('API Error'));

		await fireEvent.click(confirmButton);

		await waitFor(() => {
			expect(window.alert).toHaveBeenCalledWith('Error triggering poll');
		});
	});
});
