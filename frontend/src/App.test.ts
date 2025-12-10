import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App.svelte';
import * as api from './lib/api';

// Mock the api module
vi.mock('./lib/api', () => ({
	fetchJson: vi.fn()
}));

describe('App Component', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		// Mock API calls for Dashboard
		vi.mocked(api.fetchJson).mockResolvedValue([]);
	});

	it('renders with Navbar', () => {
		render(App);
		expect(screen.getByAltText('SentinelShare')).toBeTruthy();
	});

	it('renders Dashboard by default', async () => {
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce({ total_forwarded: 0, total_blocked: 0, total_processed: 0 })
			.mockResolvedValueOnce([]);

		render(App);

		await waitFor(() => {
			expect(screen.getByText('Total Processed')).toBeTruthy();
		});
	});

	it('switches to Settings view when settings button is clicked', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);

		render(App);

		const settingsButton = screen.getByRole('button', { name: 'Settings' });
		await fireEvent.click(settingsButton);

		await waitFor(
			() => {
				expect(screen.getByText(/Manage detection rules/i)).toBeTruthy();
			},
			{ timeout: 3000 }
		);
	});

	it('switches back to Dashboard view when dashboard button is clicked', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);

		render(App);

		// Click settings first
		const settingsButton = screen.getByRole('button', { name: 'Settings' });
		await fireEvent.click(settingsButton);

		await waitFor(
			() => {
				expect(screen.getByText(/Manage detection rules/i)).toBeTruthy();
			},
			{ timeout: 3000 }
		);

		// Click dashboard to switch back
		const dashboardButton = screen.getByRole('button', { name: 'Dashboard' });
		await fireEvent.click(dashboardButton);

		await waitFor(
			() => {
				expect(screen.getByText('Total Processed')).toBeTruthy();
			},
			{ timeout: 3000 }
		);
	});

	it('highlights active view in navbar', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);

		render(App);

		const dashboardButton = screen.getByRole('button', { name: 'Dashboard' });
		expect(dashboardButton.classList.contains('bg-white')).toBe(true);
		expect(dashboardButton.classList.contains('text-primary')).toBe(true);

		const settingsButton = screen.getByRole('button', { name: 'Settings' });
		await fireEvent.click(settingsButton);

		await waitFor(
			() => {
				expect(settingsButton.classList.contains('bg-white')).toBe(true);
				expect(settingsButton.classList.contains('text-primary')).toBe(true);
			},
			{ timeout: 3000 }
		);
	});
});
