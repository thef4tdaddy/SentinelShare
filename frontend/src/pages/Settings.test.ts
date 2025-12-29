import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import Settings from './Settings.svelte';
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

describe('Settings Component', () => {
	// Helper function to mock all API calls that happen on component mount
	const mockSettingsMountApis = () => {
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce([]) // PreferenceList preferences
			.mockResolvedValueOnce([]) // PreferenceList rules
			.mockResolvedValueOnce({ template: '' }) // EmailTemplateEditor
			.mockResolvedValueOnce([]); // checkConnections
	};

	beforeEach(() => {
		vi.clearAllMocks();
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
		mockSettingsMountApis();

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
			expect(toasts.trigger).toHaveBeenCalledWith('Poll triggered successfully', 'success');
		});
	});

	it('does not trigger poll if user cancels confirmation', async () => {
		mockSettingsMountApis();

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
		mockSettingsMountApis();

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
			expect(toasts.trigger).toHaveBeenCalledWith('Poll triggered', 'success');
		});
	});

	it('handles trigger poll error gracefully', async () => {
		mockSettingsMountApis();

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
			expect(toasts.trigger).toHaveBeenCalledWith('Error triggering poll', 'error');
		});
	});

	it('reprocessAllIgnored cancels when user declines confirmation', async () => {
		const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
		mockSettingsMountApis();

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Reprocess Ignored')).toBeTruthy();
		});

		// Clear the calls from mount
		vi.clearAllMocks();

		const reprocessButton = screen.getByText('Reprocess Ignored');
		await fireEvent.click(reprocessButton);

		// Confirm was called
		expect(confirmSpy).toHaveBeenCalledWith('Reprocess all ignored emails from last 24h?');

		// API should not be called since user declined
		expect(api.fetchJson).not.toHaveBeenCalled();

		confirmSpy.mockRestore();
	});

	it('reprocessAllIgnored successfully reprocesses emails', async () => {
		const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
		mockSettingsMountApis();

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Reprocess Ignored')).toBeTruthy();
		});

		const reprocessButton = screen.getByText('Reprocess Ignored');

		// Mock the reprocess response
		const mockResponse = { message: 'Successfully reprocessed 5 emails' };
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockResponse);

		await fireEvent.click(reprocessButton);

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith('/api/history/reprocess-all-ignored', {
				method: 'POST'
			});
			expect(toasts.trigger).toHaveBeenCalledWith('Successfully reprocessed 5 emails', 'success');
		});

		confirmSpy.mockRestore();
	});

	it('reprocessAllIgnored handles error gracefully', async () => {
		const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
		mockSettingsMountApis();

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Reprocess Ignored')).toBeTruthy();
		});

		const reprocessButton = screen.getByText('Reprocess Ignored');

		// Mock API error
		vi.mocked(api.fetchJson).mockRejectedValue(new Error('API Error'));

		await fireEvent.click(reprocessButton);

		await waitFor(() => {
			expect(toasts.trigger).toHaveBeenCalledWith('Failed to reprocess emails', 'error');
		});

		confirmSpy.mockRestore();
	});

	it('checkConnections handles error and logs to console', async () => {
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

		// Mock initial checkConnections to fail
		const error = new Error('Connection failed');
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce([]) // PreferenceList preferences
			.mockResolvedValueOnce([]) // PreferenceList rules
			.mockResolvedValueOnce({ template: '' }) // EmailTemplateEditor
			.mockRejectedValueOnce(error); // checkConnections fails

		render(Settings);

		await waitFor(() => {
			expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to test connections', error);
		});

		consoleErrorSpy.mockRestore();
	});

	it('renders Test Connections button and triggers check on click', async () => {
		mockSettingsMountApis();

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Test Connections')).toBeTruthy();
		});

		// Clear the calls from mount
		vi.clearAllMocks();

		const testButton = screen.getByText('Test Connections');

		// Mock the response for manual test
		const mockResults = [
			{ account: 'test@example.com', success: true },
			{ account: 'test2@example.com', success: false, error: 'Auth failed' }
		];
		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockResults);

		await fireEvent.click(testButton);

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith('/settings/test-connections', {
				method: 'POST'
			});
		});
	});

	it('displays successful connection with green indicator', async () => {
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce([]) // PreferenceList preferences
			.mockResolvedValueOnce([]) // PreferenceList rules
			.mockResolvedValueOnce({ template: '' }) // EmailTemplateEditor
			.mockResolvedValueOnce([{ account: 'test@example.com', success: true }]); // checkConnections

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('test@example.com')).toBeTruthy();
			expect(screen.getByText('Connected')).toBeTruthy();
		});

		// Check for green styling classes
		const accountCard = screen.getByText('test@example.com').closest('div.card');
		expect(accountCard?.classList.contains('border-l-green-500')).toBe(true);
	});

	it('displays failed connection with red indicator and error tooltip', async () => {
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce([]) // PreferenceList preferences
			.mockResolvedValueOnce([]) // PreferenceList rules
			.mockResolvedValueOnce({ template: '' }) // EmailTemplateEditor
			.mockResolvedValueOnce([
				{ account: 'test2@example.com', success: false, error: 'Authentication failed' }
			]); // checkConnections

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('test2@example.com')).toBeTruthy();
			expect(screen.getByText('Connection Failed')).toBeTruthy();
			expect(screen.getByText('Authentication failed')).toBeTruthy();
		});

		// Check for red styling classes
		const accountCard = screen.getByText('test2@example.com').closest('div.card');
		expect(accountCard?.classList.contains('border-l-red-500')).toBe(true);
	});

	it('displays multiple connection results with mixed success/failure states', async () => {
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce([]) // PreferenceList preferences
			.mockResolvedValueOnce([]) // PreferenceList rules
			.mockResolvedValueOnce({ template: '' }) // EmailTemplateEditor
			.mockResolvedValueOnce([
				{ account: 'success@example.com', success: true },
				{ account: 'failed@example.com', success: false, error: 'Timeout' },
				{ account: 'another@example.com', success: true }
			]); // checkConnections

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('success@example.com')).toBeTruthy();
			expect(screen.getByText('failed@example.com')).toBeTruthy();
			expect(screen.getByText('another@example.com')).toBeTruthy();
		});

		// Check that both "Connected" and "Connection Failed" appear
		expect(screen.getAllByText('Connected').length).toBe(2);
		expect(screen.getByText('Connection Failed')).toBeTruthy();
		expect(screen.getByText('Timeout')).toBeTruthy();
	});

	it('displays default message when no connection results exist', async () => {
		mockSettingsMountApis();

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('No accounts configured or check pending...')).toBeTruthy();
		});
	});
});
