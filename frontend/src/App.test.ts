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
			expect(screen.getByAltText('SentinelShare Logo')).toBeTruthy();
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
		await waitFor(() =>
			expect(screen.getAllByRole('button', { name: 'Settings' }).length).toBeGreaterThanOrEqual(1)
		);

		const settingsButton = screen.getAllByRole('button', { name: 'Settings' })[0];
		await fireEvent.click(settingsButton);

		await waitFor(
			() => {
				expect(screen.getByText(/Manage detection rules/i)).toBeTruthy();
			},
			{ timeout: 3000 }
		);
	});

	it(
		'switches back to Dashboard view when dashboard button is clicked',
		{ timeout: 10000 },
		async () => {
			vi.mocked(api.fetchJson).mockResolvedValue([]);

			render(App);

			// Wait for dashboard
			await waitFor(() =>
				expect(screen.getAllByRole('button', { name: 'Settings' }).length).toBeGreaterThanOrEqual(1)
			);

			// Click settings first
			const settingsButton = screen.getAllByRole('button', { name: 'Settings' })[0];
			await fireEvent.click(settingsButton);

			await waitFor(
				() => {
					expect(screen.getByText(/Manage detection rules/i)).toBeTruthy();
				},
				{ timeout: 3000 }
			);

			// Click dashboard to switch back
			const dashboardButton = screen.getAllByRole('button', { name: 'Dashboard' })[0];
			await fireEvent.click(dashboardButton);

			await waitFor(
				() => {
					expect(screen.getByText('Total Processed')).toBeTruthy();
				},
				{ timeout: 5000 }
			);
		}
	);

	it('highlights active view in navbar', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);

		render(App);

		// Wait for load
		await waitFor(() =>
			expect(screen.getAllByRole('button', { name: 'Dashboard' }).length).toBeGreaterThanOrEqual(1)
		);

		const dashboardButton = screen.getAllByRole('button', { name: 'Dashboard' })[0];
		expect(dashboardButton.classList.contains('bg-white')).toBe(true);
		expect(dashboardButton.classList.contains('text-primary')).toBe(true);

		const settingsButton = screen.getAllByRole('button', { name: 'Settings' })[0];
		await fireEvent.click(settingsButton);

		await waitFor(
			() => {
				expect(settingsButton.classList.contains('bg-white')).toBe(true);
				expect(settingsButton.classList.contains('text-primary')).toBe(true);
			},
			{ timeout: 3000 }
		);
	});

	it('renders Login view when auth check fails', async () => {
		// Override beforeEach setup for this test
		const fetchMock = vi.fn(() =>
			Promise.resolve({
				ok: false
			} as Response)
		);
		globalThis.fetch = fetchMock as unknown as typeof fetch;

		render(App);

		await waitFor(() => {
			expect(screen.getByText('SentinelShare')).toBeTruthy();
			expect(screen.getByText('Single-User Access')).toBeTruthy();
		});
	});

	it('handles auth check error and shows login', async () => {
		const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

		// Override beforeEach setup for this test
		const fetchMock = vi.fn(() => Promise.reject(new Error('Network error')));
		globalThis.fetch = fetchMock as unknown as typeof fetch;

		render(App);

		await waitFor(() => {
			expect(screen.getByText('SentinelShare')).toBeTruthy();
			expect(screen.getByText('Single-User Access')).toBeTruthy();
			expect(consoleSpy).toHaveBeenCalledWith('Auth check failed', expect.any(Error));
		});

		consoleSpy.mockRestore();
	});

	it('renders Sendee Dashboard when token is in URL', async () => {
		// Save original location
		const originalLocation = window.location;

		try {
			// Mock URL with token parameter
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			delete (window as any).location;
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			window.location = { search: '?token=test-token-123' } as any;

			// Mock successful preferences load for SendeeDashboard
			vi.mocked(api.fetchJson).mockResolvedValueOnce({
				success: true,
				email: 'test@example.com',
				blocked: [],
				allowed: []
			});

			render(App);

			// Wait for SendeeDashboard to load (should show "Forwarding Preferences" title)
			await waitFor(
				() => {
					expect(screen.getByText('Sendee Set Preferences')).toBeTruthy();
					// SendeeDashboard should be rendered without Navbar
					expect(screen.queryByAltText('SentinelShare Logo')).toBeNull();
				},
				{ timeout: 3000 }
			);
		} finally {
			// Restore original location
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			window.location = originalLocation as any;
		}
	});

	it('switches to History view when history button is clicked', async () => {
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce({ total_forwarded: 0, total_blocked: 0, total_processed: 0 })
			.mockResolvedValueOnce([])
			.mockResolvedValueOnce({
				emails: [],
				pagination: { page: 1, per_page: 50, total: 0, total_pages: 0 }
			})
			.mockResolvedValueOnce({
				total: 0,
				forwarded: 0,
				blocked: 0,
				errors: 0,
				total_amount: 0,
				status_breakdown: {}
			})
			.mockResolvedValueOnce({ runs: [] });

		render(App);

		// Wait for dashboard to load first
		await waitFor(() =>
			expect(screen.getAllByRole('button', { name: 'History' }).length).toBeGreaterThanOrEqual(1)
		);

		const historyButton = screen.getAllByRole('button', { name: 'History' })[0];
		await fireEvent.click(historyButton);

		await waitFor(
			() => {
				expect(
					screen.getByText('Complete history of email processing and automated runs.')
				).toBeTruthy();
			},
			{ timeout: 3000 }
		);
	});

	it('switches to Rules view when rules button is clicked', async () => {
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce({ total_forwarded: 0, total_blocked: 0, total_processed: 0 })
			.mockResolvedValueOnce([])
			.mockResolvedValue([]);

		render(App);

		// Wait for dashboard to load first
		await waitFor(() =>
			expect(screen.getAllByRole('button', { name: 'Rules' }).length).toBeGreaterThanOrEqual(1)
		);

		const rulesButton = screen.getAllByRole('button', { name: 'Rules' })[0];
		await fireEvent.click(rulesButton);

		await waitFor(
			() => {
				// Rules component should show "Automation Rules" heading
				expect(screen.getByText(/Automation Rules/)).toBeTruthy();
			},
			{ timeout: 3000 }
		);
	});

	it('switches to Preferences view when preferences button is clicked', async () => {
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce({ total_forwarded: 0, total_blocked: 0, total_processed: 0 })
			.mockResolvedValueOnce([])
			.mockResolvedValueOnce({
				success: true,
				email: 'admin@example.com',
				blocked: [],
				allowed: []
			});

		render(App);

		// Wait for dashboard to load first
		await waitFor(() =>
			expect(screen.getAllByRole('button', { name: 'Preferences' }).length).toBeGreaterThanOrEqual(
				1
			)
		);

		const preferencesButton = screen.getAllByRole('button', { name: 'Preferences' })[0];
		await fireEvent.click(preferencesButton);

		await waitFor(
			() => {
				// SendeeDashboard in admin mode should show "Forwarding Preferences"
				expect(screen.getByText('Sendee Set Preferences')).toBeTruthy();
				// Navbar should still be visible in admin mode
				expect(screen.queryByAltText('SentinelShare Logo')).toBeTruthy();
			},
			{ timeout: 3000 }
		);
	});

	it('calls handleLoginSuccess and switches to dashboard view', async () => {
		// Override beforeEach setup - start with failed auth to show login
		let shouldAuthSucceed = false;
		const fetchMock = vi.fn(() => {
			if (shouldAuthSucceed) {
				return Promise.resolve({
					ok: true,
					json: () => Promise.resolve({ status: 'success' })
				} as Response);
			}
			return Promise.resolve({
				ok: false
			} as Response);
		});
		globalThis.fetch = fetchMock as unknown as typeof fetch;

		render(App);

		// Wait for login to appear
		await waitFor(() => {
			expect(screen.getByText('Single-User Access')).toBeTruthy();
		});

		// Now set auth to succeed and mock Dashboard data
		shouldAuthSucceed = true;
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce({ total_forwarded: 0, total_blocked: 0, total_processed: 0 })
			.mockResolvedValueOnce([]);

		const passwordInput = screen.getByLabelText('Password');
		const submitButton = screen.getByText('Access Dashboard');

		await fireEvent.input(passwordInput, { target: { value: 'correctpass' } });
		await fireEvent.click(submitButton);

		// Should transition to dashboard (handleLoginSuccess gets called)
		await waitFor(
			() => {
				expect(screen.getByText('Total Processed')).toBeTruthy();
			},
			{ timeout: 5000 }
		);
	});
});
