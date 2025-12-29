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
	// Default mock implementation to handle all initial data fetches
	const setupDefaultMocks = () => {
		vi.mocked(api.fetchJson).mockImplementation(async (url) => {
			if (url === '/settings/accounts') return [];
			if (url === '/api/settings/preferences') return [];
			if (url === '/api/settings/rules') return [];
			if (url === '/settings/email-template') return { template: '' };
			if (url === '/settings/test-connections') return [];
			if (url.includes('trigger-poll')) return { message: 'Poll triggered' };
			if (url === '/api/settings/email-template') return { template: '' };
			return [];
		});
	};

	beforeEach(() => {
		vi.clearAllMocks();
		setupDefaultMocks();
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
		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Add New Preference')).toBeTruthy();
			expect(screen.getByText('Add New Rule')).toBeTruthy();
		});
	});

	it('triggers poll when Run Now is clicked and confirmed', async () => {
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

		// Override default mock for specific return expectation if needed,
		// strictly speaking setupDefaultMocks handles it but let's be explicit if checking return value
		vi.mocked(api.fetchJson).mockImplementation(async (url) => {
			if (url === '/settings/trigger-poll') return { message: 'Poll triggered successfully' };
			// Fallback to defaults
			if (url === '/settings/accounts') return [];
			if (url === '/api/settings/preferences') return [];
			if (url === '/api/settings/rules') return [];
			if (url === '/settings/email-template') return { template: '' };
			if (url === '/settings/test-connections') return [];
			if (url === '/api/settings/email-template') return { template: '' };
			if (url.includes('trigger-poll')) return { message: 'Poll triggered' };
			return {};
		});

		await fireEvent.click(confirmButton);

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith('/settings/trigger-poll', {
				method: 'POST'
			});
			expect(toasts.trigger).toHaveBeenCalledWith('Poll triggered successfully', 'success');
		});
	});

	it('does not trigger poll if user cancels confirmation', async () => {
		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Run Now')).toBeTruthy();
		});

		// Clear the calls from mount
		vi.clearAllMocks();
		// Restore defaults just in case clearAllMocks wipes implementations (it doesn't wipe implementations usually, but clearAllMocks clears call history)
		setupDefaultMocks();

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
		render(Settings);

		const runNowButton = screen.getByText('Run Now');
		await fireEvent.click(runNowButton);

		await waitFor(() => {
			expect(screen.getByText('Run Email Check')).toBeTruthy();
		});

		const buttons = screen.getAllByRole('button', { name: 'Run Now' });
		const confirmButton = buttons[1];

		// Mock empty response
		vi.mocked(api.fetchJson).mockImplementation(async (url) => {
			if (url === '/settings/trigger-poll') return {};
			if (url === '/settings/accounts') return [];
			if (url === '/api/settings/preferences') return [];
			if (url === '/api/settings/rules') return [];
			if (url === '/settings/email-template') return { template: '' };
			if (url === '/settings/test-connections') return [];
			return {};
		});

		await fireEvent.click(confirmButton);

		await waitFor(() => {
			expect(toasts.trigger).toHaveBeenCalledWith('Poll triggered', 'success');
		});
	});

	it('handles trigger poll error gracefully', async () => {
		render(Settings);

		const runNowButton = screen.getByText('Run Now');
		await fireEvent.click(runNowButton);

		await waitFor(() => {
			expect(screen.getByText('Run Email Check')).toBeTruthy();
		});

		const buttons = screen.getAllByRole('button', { name: 'Run Now' });
		const confirmButton = buttons[1];

		// Mock the trigger-poll API error
		vi.mocked(api.fetchJson).mockImplementation(async (url) => {
			if (url === '/settings/trigger-poll') throw new Error('API Error');
			if (url === '/settings/accounts') return [];
			if (url === '/api/settings/preferences') return [];
			if (url === '/api/settings/rules') return [];
			if (url === '/settings/email-template') return { template: '' };
			if (url === '/settings/test-connections') return [];
			return {};
		});

		await fireEvent.click(confirmButton);

		await waitFor(() => {
			expect(toasts.trigger).toHaveBeenCalledWith('Error triggering poll', 'error');
		});
	});

	it('reprocessAllIgnored cancels when user declines confirmation', async () => {
		const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Reprocess Ignored')).toBeTruthy();
		});

		vi.clearAllMocks();
		setupDefaultMocks();

		const reprocessButton = screen.getByText('Reprocess Ignored');
		await fireEvent.click(reprocessButton);

		expect(confirmSpy).toHaveBeenCalledWith('Reprocess all ignored emails from last 24h?');
		expect(api.fetchJson).not.toHaveBeenCalled();

		confirmSpy.mockRestore();
	});

	it('reprocessAllIgnored successfully reprocesses emails', async () => {
		const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Reprocess Ignored')).toBeTruthy();
		});

		const reprocessButton = screen.getByText('Reprocess Ignored');

		vi.mocked(api.fetchJson).mockImplementation(async (url) => {
			if (url === '/api/history/reprocess-all-ignored')
				return { message: 'Successfully reprocessed 5 emails' };
			if (url === '/settings/accounts') return [];
			if (url === '/api/settings/preferences') return [];
			if (url === '/api/settings/rules') return [];
			if (url === '/settings/email-template') return { template: '' };
			if (url === '/settings/test-connections') return [];
			return {};
		});

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
		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Reprocess Ignored')).toBeTruthy();
		});

		const reprocessButton = screen.getByText('Reprocess Ignored');

		vi.mocked(api.fetchJson).mockImplementation(async (url) => {
			if (url === '/api/history/reprocess-all-ignored') throw new Error('API Error');
			if (url === '/settings/accounts') return [];
			if (url === '/api/settings/preferences') return [];
			if (url === '/api/settings/rules') return [];
			if (url === '/settings/email-template') return { template: '' };
			if (url === '/settings/test-connections') return [];
			return {};
		});

		await fireEvent.click(reprocessButton);

		await waitFor(() => {
			expect(toasts.trigger).toHaveBeenCalledWith('Failed to reprocess emails', 'error');
		});

		confirmSpy.mockRestore();
	});

	it('checkConnections handles error and logs to console', async () => {
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

		const error = new Error('Connection failed');
		vi.mocked(api.fetchJson).mockImplementation(async (url) => {
			if (url === '/settings/test-connections') throw error;
			if (url === '/settings/accounts') return [];
			if (url === '/api/settings/preferences') return [];
			if (url === '/api/settings/rules') return [];
			if (url === '/settings/email-template') return { template: '' };
			return [];
		});

		render(Settings);

		await waitFor(() => {
			expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to test connections', error);
		});

		consoleErrorSpy.mockRestore();
	});

	it('renders Test Connections button and triggers check on click', async () => {
		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Test Connections')).toBeTruthy();
		});

		vi.clearAllMocks();
		// Setup mock for manual click
		const mockResults = [
			{ account: 'test@example.com', success: true },
			{ account: 'test2@example.com', success: false, error: 'Auth failed' }
		];
		vi.mocked(api.fetchJson).mockImplementation(async (url) => {
			if (url === '/settings/test-connections') return mockResults;
			if (url === '/settings/accounts') return [];
			if (url === '/api/settings/preferences') return [];
			if (url === '/api/settings/rules') return [];
			if (url === '/settings/email-template') return { template: '' };
			return [];
		});

		const testButton = screen.getByText('Test Connections');
		await fireEvent.click(testButton);

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith('/settings/test-connections', {
				method: 'POST'
			});
		});
	});

	it('displays successful connection with green indicator', async () => {
		vi.mocked(api.fetchJson).mockImplementation(async (url) => {
			if (url === '/settings/test-connections')
				return [{ account: 'test@example.com', success: true }];
			if (url === '/settings/accounts') return [];
			if (url === '/api/settings/preferences') return [];
			if (url === '/api/settings/rules') return [];
			if (url === '/settings/email-template') return { template: '' };
			return [];
		});

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('test@example.com')).toBeTruthy();
			expect(screen.getByText('Connected')).toBeTruthy();
		});

		const accountCard = screen.getByText('test@example.com').closest('div.card');
		expect(accountCard?.classList.contains('border-l-green-500')).toBe(true);
	});

	it('displays failed connection with red indicator and error tooltip', async () => {
		vi.mocked(api.fetchJson).mockImplementation(async (url) => {
			if (url === '/settings/test-connections')
				return [{ account: 'test2@example.com', success: false, error: 'Authentication failed' }];
			if (url === '/settings/accounts') return [];
			if (url === '/api/settings/preferences') return [];
			if (url === '/api/settings/rules') return [];
			if (url === '/settings/email-template') return { template: '' };
			return [];
		});

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('test2@example.com')).toBeTruthy();
			expect(screen.getByText('Connection Failed')).toBeTruthy();
			expect(screen.getByText('Authentication failed')).toBeTruthy();
		});

		const accountCard = screen.getByText('test2@example.com').closest('div.card');
		expect(accountCard?.classList.contains('border-l-red-500')).toBe(true);
	});

	it('displays multiple connection results with mixed success/failure states', async () => {
		vi.mocked(api.fetchJson).mockImplementation(async (url) => {
			if (url === '/settings/test-connections')
				return [
					{ account: 'success@example.com', success: true },
					{ account: 'failed@example.com', success: false, error: 'Timeout' },
					{ account: 'another@example.com', success: true }
				];
			if (url === '/settings/accounts') return [];
			if (url === '/api/settings/preferences') return [];
			if (url === '/api/settings/rules') return [];
			if (url === '/settings/email-template') return { template: '' };
			return [];
		});

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('success@example.com')).toBeTruthy();
			expect(screen.getByText('failed@example.com')).toBeTruthy();
			expect(screen.getByText('another@example.com')).toBeTruthy();
		});

		expect(screen.getAllByText('Connected').length).toBe(2);
		expect(screen.getByText('Connection Failed')).toBeTruthy();
		expect(screen.getByText('Timeout')).toBeTruthy();
	});

	it('displays default message when no connection results exist', async () => {
		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('No accounts configured or check pending...')).toBeTruthy();
		});
	});
});
