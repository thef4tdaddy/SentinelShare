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
		// Mock API calls for Dashboard and Auth
		vi.mocked(api.fetchJson).mockResolvedValue([]);

		// Mock globally for fetch if it's used directly in onMount
		globalThis.fetch = vi.fn(() =>
			Promise.resolve({
				ok: true,
				json: () => Promise.resolve({ authenticated: true })
			})
		) as unknown as typeof fetch;
	});

	it('renders with Navbar', async () => {
		render(App);
		// Wait for loading to finish
		await waitFor(() => {
			expect(screen.getByAltText('SentinelShare')).toBeTruthy();
		});
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

		// Wait for dashboard to load first
		await waitFor(() => expect(screen.getByRole('button', { name: 'Settings' })).toBeTruthy());

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

		// Wait for dashboard
		await waitFor(() => expect(screen.getByRole('button', { name: 'Settings' })).toBeTruthy());

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

		// Wait for load
		await waitFor(() => expect(screen.getByRole('button', { name: 'Dashboard' })).toBeTruthy());

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
