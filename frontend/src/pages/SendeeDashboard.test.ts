import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import SendeeDashboard from './SendeeDashboard.svelte';
import * as api from '../lib/api';

// Mock the api module
vi.mock('../lib/api', () => ({
	fetchJson: vi.fn()
}));

describe('SendeeDashboard Component', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('renders title and description', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('Forwarding Preferences')).toBeTruthy();
		});
	});

	it('displays loading state on mount', () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		expect(screen.getByText('Loading your secure dashboard...')).toBeTruthy();
	});

	it('loads preferences with token on mount', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: ['spam@example.com'],
			allowed: ['trusted@example.com']
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith(
				'/actions/preferences-for-sendee?token=test-token'
			);
		});
	});

	it('loads preferences without token for admin', async () => {
		const mockPreferences = {
			success: true,
			email: 'admin@example.com',
			blocked: [],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: null, isAdmin: true } });

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith('/actions/preferences-for-sendee');
		});
	});

	it('displays user email after loading preferences', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText(/user@example.com/)).toBeTruthy();
		});
	});

	it('displays admin message when isAdmin is true', async () => {
		const mockPreferences = {
			success: true,
			email: 'admin@example.com',
			blocked: [],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: null, isAdmin: true } });

		await waitFor(() => {
			expect(screen.getByText('Manage global forwarding preferences.')).toBeTruthy();
		});
	});

	it('displays error state when loading fails', async () => {
		vi.mocked(api.fetchJson).mockRejectedValueOnce(new Error('Unauthorized'));

		render(SendeeDashboard, { props: { token: 'invalid-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('Access Denied')).toBeTruthy();
			expect(screen.getByText('Unauthorized')).toBeTruthy();
		});
	});

	it('displays error when API returns success: false', async () => {
		const mockPreferences = {
			success: false
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('Access Denied')).toBeTruthy();
			expect(screen.getByText('Failed to load preferences.')).toBeTruthy();
		});
	});

	it('displays allowed senders', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: ['trusted1@example.com', 'trusted2@example.com']
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('trusted1@example.com')).toBeTruthy();
			expect(screen.getByText('trusted2@example.com')).toBeTruthy();
		});
	});

	it('displays blocked senders', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: ['spam1@example.com', 'spam2@example.com'],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('spam1@example.com')).toBeTruthy();
			expect(screen.getByText('spam2@example.com')).toBeTruthy();
		});
	});

	it('displays empty state for allowed senders', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('No senders in your allow-list.')).toBeTruthy();
		});
	});

	it('displays empty state for blocked senders', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('No blocked senders yet.')).toBeTruthy();
		});
	});

	it('removes allowed sender when X button is clicked', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: ['trusted@example.com']
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		const { container } = render(SendeeDashboard, {
			props: { token: 'test-token', isAdmin: false }
		});

		await waitFor(() => {
			expect(screen.getByText('trusted@example.com')).toBeTruthy();
		});

		// Find the X button in the allowed sender badge
		const allowedSection = container.querySelector('.bg-emerald-100.text-emerald-700');
		const xButton = allowedSection?.querySelector('button');

		expect(xButton).toBeTruthy();

		if (xButton) {
			await fireEvent.click(xButton);

			await waitFor(() => {
				expect(screen.getByText('No senders in your allow-list.')).toBeTruthy();
			});
		}
	});

	it('removes blocked sender when X button is clicked', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: ['spam@example.com'],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		const { container } = render(SendeeDashboard, {
			props: { token: 'test-token', isAdmin: false }
		});

		await waitFor(() => {
			expect(screen.getByText('spam@example.com')).toBeTruthy();
		});

		// Find all buttons and get the one in the blocked section
		const buttons = container.querySelectorAll('button');
		let blockedButton: Element | null = null;

		// Find the button that's within a badge containing 'spam@example.com'
		buttons.forEach((button) => {
			const badge = button.closest('.badge');
			if (badge && badge.textContent?.includes('spam@example.com')) {
				blockedButton = button;
			}
		});

		expect(blockedButton).toBeTruthy();

		if (blockedButton) {
			await fireEvent.click(blockedButton);

			await waitFor(() => {
				expect(screen.getByText('No blocked senders yet.')).toBeTruthy();
			});
		}
	});

	it('saves changes successfully', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		const mockSaveResponse = {
			success: true
		};

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockPreferences)
			.mockResolvedValueOnce(mockSaveResponse);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('Save Preferences')).toBeTruthy();
		});

		const saveButton = screen.getByText('Save Preferences');
		await fireEvent.click(saveButton);

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith('/actions/update-preferences', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					token: 'test-token',
					blocked_senders: [],
					allowed_senders: []
				})
			});
		});
	});

	it('displays success message after saving', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		const mockSaveResponse = {
			success: true
		};

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockPreferences)
			.mockResolvedValueOnce(mockSaveResponse);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('Save Preferences')).toBeTruthy();
		});

		const saveButton = screen.getByText('Save Preferences');
		await fireEvent.click(saveButton);

		await waitFor(() => {
			expect(screen.getByText('Preferences updated successfully!')).toBeTruthy();
		});
	});

	it('displays saving state when saving', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		// Create a promise we can control
		let resolveSave: (value: unknown) => void;
		const savePromise = new Promise((resolve) => {
			resolveSave = resolve;
		});

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockPreferences)
			.mockReturnValueOnce(savePromise as Promise<never>);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('Save Preferences')).toBeTruthy();
		});

		const saveButton = screen.getByText('Save Preferences');
		await fireEvent.click(saveButton);

		// Check for saving state
		await waitFor(() => {
			expect(screen.getByText('Saving...')).toBeTruthy();
		});

		// Resolve the promise to clean up
		resolveSave!({ success: true });
	});

	it('handles save error gracefully', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockPreferences)
			.mockRejectedValueOnce(new Error('Failed to save changes.'));

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('Save Preferences')).toBeTruthy();
		});

		const saveButton = screen.getByText('Save Preferences');
		await fireEvent.click(saveButton);

		await waitFor(() => {
			expect(screen.getByText('Failed to save changes.')).toBeTruthy();
		});
	});

	it('displays Return Home button in error state', async () => {
		vi.mocked(api.fetchJson).mockRejectedValueOnce(new Error('Unauthorized'));

		render(SendeeDashboard, { props: { token: 'invalid-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('Return Home')).toBeTruthy();
		});
	});

	it('handles empty blocked and allowed arrays from API', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com'
			// blocked and allowed are undefined
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('No senders in your allow-list.')).toBeTruthy();
			expect(screen.getByText('No blocked senders yet.')).toBeTruthy();
		});
	});

	it('renders Always Forward section with correct styling', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('Always Forward')).toBeTruthy();
			expect(screen.getByText('Receipts from these senders are always allowed.')).toBeTruthy();
		});
	});

	it('renders Blocked Senders section with correct styling', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('Blocked Senders')).toBeTruthy();
			expect(
				screen.getByText('SentinelShare will ignore all emails from these senders.')
			).toBeTruthy();
		});
	});

	it('encodes token properly in URL', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		const specialToken = 'test+token=with&special?chars';
		render(SendeeDashboard, { props: { token: specialToken, isAdmin: false } });

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith(
				expect.stringContaining(encodeURIComponent(specialToken))
			);
		});
	});

	it('shows correct description text for non-admin users', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText(/Manage how SentinelShare handles receipts/)).toBeTruthy();
		});
	});

	it('disables save button when saving', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: []
		};

		// Create a promise we can control
		let resolveSave: (value: unknown) => void;
		const savePromise = new Promise((resolve) => {
			resolveSave = resolve;
		});

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockPreferences)
			.mockReturnValueOnce(savePromise as Promise<never>);

		render(SendeeDashboard, { props: { token: 'test-token', isAdmin: false } });

		await waitFor(() => {
			expect(screen.getByText('Save Preferences')).toBeTruthy();
		});

		const saveButton = screen.getByText('Save Preferences') as HTMLButtonElement;
		await fireEvent.click(saveButton);

		await waitFor(() => {
			const savingButton = screen.getByText('Saving...').closest('button') as HTMLButtonElement;
			expect(savingButton.disabled).toBe(true);
		});

		// Resolve the promise to clean up
		resolveSave!({ success: true });
	});

	it('removes sender from allowed when clicking X button', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: [],
			allowed: ['trusted@example.com']
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		const { container } = render(SendeeDashboard, {
			props: { token: 'test-token', isAdmin: false }
		});

		await waitFor(() => {
			expect(screen.getByText('trusted@example.com')).toBeTruthy();
		});

		// Find and click the X button to remove from allowed
		const allowedBadge = container.querySelector('.bg-emerald-100.text-emerald-700');
		const xButton = allowedBadge?.querySelector('button');

		expect(xButton).toBeTruthy();

		if (xButton) {
			// Click removes from allowed
			await fireEvent.click(xButton);

			// Verify it's not in allowed anymore
			await waitFor(() => {
				expect(screen.getByText('No senders in your allow-list.')).toBeTruthy();
			});
		}
	});

	it('removes sender from blocked when clicking X button', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: ['spam@example.com'],
			allowed: []
		};

		vi.mocked(api.fetchJson).mockResolvedValueOnce(mockPreferences);

		const { container } = render(SendeeDashboard, {
			props: { token: 'test-token', isAdmin: false }
		});

		await waitFor(() => {
			expect(screen.getByText('spam@example.com')).toBeTruthy();
		});

		// Find and click the X button to remove from blocked
		const badges = Array.from(container.querySelectorAll('.badge'));
		const blockedBadge = badges.find(
			(badge) =>
				badge.textContent?.includes('spam@example.com') && badge.className.includes('bg-danger')
		);
		const xButton = blockedBadge?.querySelector('button');

		expect(xButton).toBeTruthy();

		if (xButton) {
			// Click removes from blocked
			await fireEvent.click(xButton);

			// Verify it's not in blocked anymore
			await waitFor(() => {
				expect(screen.getByText('No blocked senders yet.')).toBeTruthy();
			});
		}
	});

	it('verifies blocked list state after removing sender', async () => {
		const mockPreferences = {
			success: true,
			email: 'user@example.com',
			blocked: ['spam@example.com'],
			allowed: ['initial-trusted@example.com']
		};

		const mockSaveResponse = {
			success: true
		};

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockPreferences)
			.mockResolvedValueOnce(mockSaveResponse);

		const { container } = render(SendeeDashboard, {
			props: { token: 'test-token', isAdmin: false }
		});

		await waitFor(() => {
			expect(screen.getByText('spam@example.com')).toBeTruthy();
		});

		// Find X button on blocked sender to remove it
		const badges = Array.from(container.querySelectorAll('.badge'));
		const blockedBadge = badges.find(
			(badge) =>
				badge.textContent?.includes('spam@example.com') && badge.className.includes('bg-danger')
		);
		const xButton = blockedBadge?.querySelector('button');

		expect(xButton).toBeTruthy();

		if (xButton) {
			// Click removes from blocked
			await fireEvent.click(xButton);

			// Save the changes to verify the state
			const saveButton = screen.getByText('Save Preferences');
			await fireEvent.click(saveButton);

			await waitFor(() => {
				expect(api.fetchJson).toHaveBeenCalledWith(
					'/actions/update-preferences',
					expect.objectContaining({
						body: JSON.stringify({
							token: 'test-token',
							blocked_senders: [],
							allowed_senders: ['initial-trusted@example.com']
						})
					})
				);
			});
		}
	});
});
