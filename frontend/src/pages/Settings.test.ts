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
		window.confirm = vi.fn(() => true);
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
		vi.mocked(api.fetchJson).mockResolvedValue(mockResponse);

		render(Settings);

		const runNowButton = screen.getByText('Run Now');
		await fireEvent.click(runNowButton);

		await waitFor(() => {
			expect(window.confirm).toHaveBeenCalledWith('Run email check now?');
			expect(api.fetchJson).toHaveBeenCalledWith('/settings/trigger-poll', {
				method: 'POST'
			});
			expect(window.alert).toHaveBeenCalledWith('Poll triggered successfully');
		});
	});

	it('does not trigger poll if user cancels confirmation', async () => {
		window.confirm = vi.fn(() => false);
		vi.mocked(api.fetchJson).mockResolvedValue([]);

		render(Settings);

		await waitFor(() => {
			expect(screen.getByText('Run Now')).toBeTruthy();
		});

		// Clear the calls from PreferenceList mount
		vi.clearAllMocks();

		const runNowButton = screen.getByText('Run Now');
		await fireEvent.click(runNowButton);

		expect(window.confirm).toHaveBeenCalledWith('Run email check now?');
		expect(api.fetchJson).not.toHaveBeenCalled();
	});

	it('shows default message if API response has no message', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue({});

		render(Settings);

		const runNowButton = screen.getByText('Run Now');
		await fireEvent.click(runNowButton);

		await waitFor(() => {
			expect(window.alert).toHaveBeenCalledWith('Poll triggered');
		});
	});

	it('handles trigger poll error gracefully', async () => {
		vi.mocked(api.fetchJson).mockRejectedValue(new Error('API Error'));

		render(Settings);

		const runNowButton = screen.getByText('Run Now');
		await fireEvent.click(runNowButton);

		await waitFor(() => {
			expect(window.alert).toHaveBeenCalledWith('Error triggering poll');
		});
	});
});
