import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import History from './History.svelte';
import * as api from '../lib/api';

// Mock the api module
vi.mock('../lib/api', () => ({
	fetchJson: vi.fn()
}));

describe('History Component', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('renders history page with title', async () => {
		const mockHistory = {
			emails: [],
			pagination: { page: 1, per_page: 50, total: 0, total_pages: 0 }
		};
		const mockStats = {
			total: 0,
			forwarded: 0,
			blocked: 0,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			expect(screen.getByText('History')).toBeTruthy();
			expect(
				screen.getByText('Complete history of email processing and automated runs.')
			).toBeTruthy();
		});
	});

	it('displays stats cards correctly', async () => {
		const mockHistory = {
			emails: [],
			pagination: { page: 1, per_page: 50, total: 0, total_pages: 0 }
		};
		const mockStats = {
			total: 100,
			forwarded: 60,
			blocked: 35,
			errors: 5,
			total_amount: 1234.56,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			expect(screen.getByText('Total Processed')).toBeTruthy();
			expect(screen.getByText('100')).toBeTruthy();
			expect(screen.getByText('60')).toBeTruthy();
			expect(screen.getByText('35')).toBeTruthy();
			expect(screen.getByText('5')).toBeTruthy();
		});
	});

	it('renders email history table with data', async () => {
		const mockHistory = {
			emails: [
				{
					id: 1,
					email_id: 'test1@example.com',
					subject: 'Amazon Receipt',
					sender: 'order@amazon.com',
					received_at: '2024-01-01T10:00:00Z',
					processed_at: '2024-01-01T10:01:00Z',
					status: 'forwarded',
					account_email: 'user@example.com',
					category: 'shopping',
					amount: 49.99,
					reason: 'Detected as receipt'
				}
			],
			pagination: { page: 1, per_page: 50, total: 1, total_pages: 1 }
		};
		const mockStats = {
			total: 1,
			forwarded: 1,
			blocked: 0,
			errors: 0,
			total_amount: 49.99,
			status_breakdown: { forwarded: 1 }
		};
		const mockRuns = { runs: [] };

		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			expect(screen.getByText('Amazon Receipt')).toBeTruthy();
			expect(screen.getByText('order@amazon.com')).toBeTruthy();
			expect(screen.getByText('shopping')).toBeTruthy();
		});
	});

	it('shows empty state when no emails', async () => {
		const mockHistory = {
			emails: [],
			pagination: { page: 1, per_page: 50, total: 0, total_pages: 0 }
		};
		const mockStats = {
			total: 0,
			forwarded: 0,
			blocked: 0,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			expect(screen.getByText('No emails found.')).toBeTruthy();
		});
	});

	it('switches between tabs', async () => {
		const mockHistory = {
			emails: [],
			pagination: { page: 1, per_page: 50, total: 0, total_pages: 0 }
		};
		const mockStats = {
			total: 0,
			forwarded: 0,
			blocked: 0,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = {
			runs: [
				{
					run_time: '2024-01-01T10:00:00Z',
					first_processed: '2024-01-01T10:00:00Z',
					last_processed: '2024-01-01T10:05:00Z',
					total_emails: 10,
					forwarded: 7,
					blocked: 2,
					errors: 1,
					email_ids: [1, 2, 3]
				}
			]
		};

		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			expect(screen.getByText('All Emails')).toBeTruthy();
			expect(screen.getByText('Processing Runs')).toBeTruthy();
		});

		// Click on Processing Runs tab
		const runsTab = screen.getByText('Processing Runs');
		await fireEvent.click(runsTab);

		await waitFor(() => {
			expect(screen.getByText('Recent Processing Runs')).toBeTruthy();
		});
	});

	it('displays processing runs correctly', async () => {
		const mockHistory = {
			emails: [],
			pagination: { page: 1, per_page: 50, total: 0, total_pages: 0 }
		};
		const mockStats = {
			total: 0,
			forwarded: 0,
			blocked: 0,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = {
			runs: [
				{
					run_time: '2024-01-01T10:00:00Z',
					first_processed: '2024-01-01T10:00:00Z',
					last_processed: '2024-01-01T10:05:00Z',
					total_emails: 15,
					forwarded: 10,
					blocked: 4,
					errors: 1,
					email_ids: [1, 2, 3]
				}
			]
		};

		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		// Switch to runs tab
		const runsTab = screen.getByText('Processing Runs');
		await fireEvent.click(runsTab);

		await waitFor(() => {
			expect(screen.getByText('15 emails')).toBeTruthy();
		});
	});

	it('calls correct API endpoints on mount', async () => {
		const mockHistory = {
			emails: [],
			pagination: { page: 1, per_page: 50, total: 0, total_pages: 0 }
		};
		const mockStats = {
			total: 0,
			forwarded: 0,
			blocked: 0,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith(expect.stringContaining('/history/emails'));
			expect(api.fetchJson).toHaveBeenCalledWith('/history/stats');
			expect(api.fetchJson).toHaveBeenCalledWith('/history/runs');
		});
	});

	it('handles API errors gracefully', async () => {
		const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

		(api.fetchJson as any).mockRejectedValueOnce(new Error('API Error'));

		render(History);

		await waitFor(() => {
			expect(consoleSpy).toHaveBeenCalledWith('Failed to load history', expect.any(Error));
		});

		consoleSpy.mockRestore();
	});

	it('renders filter controls', async () => {
		const mockHistory = {
			emails: [],
			pagination: { page: 1, per_page: 50, total: 0, total_pages: 0 }
		};
		const mockStats = {
			total: 0,
			forwarded: 0,
			blocked: 0,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			expect(screen.getByLabelText('Status')).toBeTruthy();
			expect(screen.getByLabelText('From Date')).toBeTruthy();
			expect(screen.getByLabelText('To Date')).toBeTruthy();
			expect(screen.getByText('Clear Filters')).toBeTruthy();
		});
	});

	it('displays pagination when multiple pages exist', async () => {
		const mockHistory = {
			emails: [
				{
					id: 1,
					email_id: 'test1@example.com',
					subject: 'Test Email',
					sender: 'test@example.com',
					received_at: '2024-01-01T10:00:00Z',
					processed_at: '2024-01-01T10:01:00Z',
					status: 'forwarded',
					account_email: 'user@example.com',
					category: 'test',
					amount: 10.0,
					reason: 'Test'
				}
			],
			pagination: { page: 1, per_page: 50, total: 150, total_pages: 3 }
		};
		const mockStats = {
			total: 150,
			forwarded: 100,
			blocked: 50,
			errors: 0,
			total_amount: 1000.0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			expect(screen.getByText('Page 1 of 3 (150 total)')).toBeTruthy();
			expect(screen.getByText('Previous')).toBeTruthy();
			expect(screen.getByText('Next')).toBeTruthy();
		});
	});

	it('shows empty state for runs when no runs available', async () => {
		const mockHistory = {
			emails: [],
			pagination: { page: 1, per_page: 50, total: 0, total_pages: 0 }
		};
		const mockStats = {
			total: 0,
			forwarded: 0,
			blocked: 0,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		// Switch to runs tab
		const runsTab = screen.getByText('Processing Runs');
		await fireEvent.click(runsTab);

		await waitFor(() => {
			expect(screen.getByText('No processing runs found.')).toBeTruthy();
		});
	});

	it('calls API with filter parameters when status filter changes', async () => {
		const mockHistory = {
			emails: [],
			pagination: { page: 1, per_page: 50, total: 0, total_pages: 0 }
		};
		const mockStats = {
			total: 0,
			forwarded: 0,
			blocked: 0,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		// Mock returns for initial load and filter change
		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		// Wait for initial load
		await waitFor(() => {
			expect(screen.getByLabelText('Status')).toBeTruthy();
		});

		// Clear previous calls
		vi.clearAllMocks();

		// Change status filter
		const statusSelect = screen.getByLabelText('Status') as HTMLSelectElement;
		await fireEvent.change(statusSelect, { target: { value: 'forwarded' } });

		// Verify API was called with status parameter
		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith(
				expect.stringContaining('status=forwarded')
			);
		});
	});

	it('clears filters and refreshes data when Clear Filters is clicked', async () => {
		const mockHistory = {
			emails: [],
			pagination: { page: 1, per_page: 50, total: 0, total_pages: 0 }
		};
		const mockStats = {
			total: 0,
			forwarded: 0,
			blocked: 0,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		// Mock returns for initial load, filter change, and clear filters
		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		// Wait for initial load
		await waitFor(() => {
			expect(screen.getByText('Clear Filters')).toBeTruthy();
		});

		// Set a filter first
		const statusSelect = screen.getByLabelText('Status') as HTMLSelectElement;
		await fireEvent.change(statusSelect, { target: { value: 'forwarded' } });

		// Clear previous calls
		vi.clearAllMocks();

		// Click Clear Filters
		const clearButton = screen.getByText('Clear Filters');
		await fireEvent.click(clearButton);

		// Verify filters were reset and API called without filter params
		await waitFor(() => {
			expect(statusSelect.value).toBe('');
			expect(api.fetchJson).toHaveBeenCalled();
		});
	});

	it('resets page to 1 when filters change', async () => {
		const mockHistory = {
			emails: [],
			pagination: { page: 1, per_page: 50, total: 0, total_pages: 0 }
		};
		const mockStats = {
			total: 0,
			forwarded: 0,
			blocked: 0,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		// Mock returns for initial load and filter change
		(api.fetchJson as any)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		// Wait for initial load
		await waitFor(() => {
			expect(screen.getByLabelText('Status')).toBeTruthy();
		});

		// Clear previous calls
		vi.clearAllMocks();

		// Change filter
		const statusSelect = screen.getByLabelText('Status') as HTMLSelectElement;
		await fireEvent.change(statusSelect, { target: { value: 'blocked' } });

		// Verify API was called with page=1
		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith(
				expect.stringMatching(/page=1/)
			);
		});
	});
});
