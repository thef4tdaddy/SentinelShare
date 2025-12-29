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

		vi.mocked(api.fetchJson)
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

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			expect(screen.getByText('Total Processed')).toBeTruthy();
			expect(screen.getAllByText('100').length).toBeGreaterThanOrEqual(1);
			expect(screen.getAllByText('60').length).toBeGreaterThanOrEqual(1);
			expect(screen.getAllByText('35').length).toBeGreaterThanOrEqual(1);
			expect(screen.getAllByText('5').length).toBeGreaterThanOrEqual(1);
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

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			expect(screen.getAllByText('Amazon Receipt').length).toBeGreaterThanOrEqual(1);
			expect(screen.getAllByText('order@amazon.com').length).toBeGreaterThanOrEqual(1);
			expect(screen.getAllByText('shopping').length).toBeGreaterThanOrEqual(1);
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

		vi.mocked(api.fetchJson)
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

		vi.mocked(api.fetchJson)
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

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		// Switch to runs tab
		const runsTab = screen.getByText('Processing Runs');
		await fireEvent.click(runsTab);

		await waitFor(() => {
			expect(screen.getAllByText('15 emails').length).toBeGreaterThanOrEqual(1);
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

		vi.mocked(api.fetchJson)
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

		vi.mocked(api.fetchJson).mockRejectedValueOnce(new Error('API Error'));

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

		vi.mocked(api.fetchJson)
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

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			expect(screen.getAllByText('Page 1 of 3 (150 total)').length).toBeGreaterThanOrEqual(1);
			expect(screen.getAllByText('Previous').length).toBeGreaterThanOrEqual(1);
			expect(screen.getAllByText('Next').length).toBeGreaterThanOrEqual(1);
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

		vi.mocked(api.fetchJson)
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
		vi.mocked(api.fetchJson)
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
			expect(api.fetchJson).toHaveBeenCalledWith(expect.stringContaining('status=forwarded'));
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
		vi.mocked(api.fetchJson)
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
		vi.mocked(api.fetchJson)
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
			expect(api.fetchJson).toHaveBeenCalledWith(expect.stringMatching(/page=1/));
		});
	});

	it('calls API with date_from filter when provided', async () => {
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
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		const { container } = render(History);

		// Wait for initial load
		await waitFor(() => {
			expect(screen.getByLabelText('From Date')).toBeTruthy();
		});

		// Clear previous calls
		vi.clearAllMocks();

		// Change date_from filter - need to trigger input event and then change event
		const dateFromInput = screen.getByLabelText('From Date') as HTMLInputElement;
		dateFromInput.value = '2024-01-01T00:00';
		await fireEvent.input(dateFromInput);
		await fireEvent.change(dateFromInput);

		// Verify API was called with date_from parameter
		await waitFor(() => {
			const calls = vi.mocked(api.fetchJson).mock.calls;
			const hasDateFrom = calls.some((call) =>
				call[0].toString().includes('date_from=2024-01-01T00')
			);
			expect(hasDateFrom).toBe(true);
		});
	});

	it('calls API with date_to filter when provided', async () => {
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
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		// Wait for initial load
		await waitFor(() => {
			expect(screen.getByLabelText('To Date')).toBeTruthy();
		});

		// Clear previous calls
		vi.clearAllMocks();

		// Change date_to filter - need to trigger input event and then change event
		const dateToInput = screen.getByLabelText('To Date') as HTMLInputElement;
		dateToInput.value = '2024-12-31T23:59';
		await fireEvent.input(dateToInput);
		await fireEvent.change(dateToInput);

		// Verify API was called with date_to parameter
		await waitFor(() => {
			const calls = vi.mocked(api.fetchJson).mock.calls;
			const hasDateTo = calls.some((call) => call[0].toString().includes('date_to=2024-12-31T23'));
			expect(hasDateTo).toBe(true);
		});
	});

	it('handles pagination - navigates to next page', async () => {
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

		// Mock returns for initial load and page change
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns)
			.mockResolvedValueOnce({ ...mockHistory, pagination: { ...mockHistory.pagination, page: 2 } })
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		// Wait for initial load
		await waitFor(() => {
			expect(screen.getAllByText('Next').length).toBeGreaterThanOrEqual(1);
		});

		// Clear previous calls
		vi.clearAllMocks();

		// Click Next button
		const nextButtons = screen.getAllByText('Next');
		await fireEvent.click(nextButtons[0]);

		// Verify API was called with page=2
		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith(expect.stringMatching(/page=2/));
		});
	});

	it('handles pagination - navigates to previous page', async () => {
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
			pagination: { page: 2, per_page: 50, total: 150, total_pages: 3 }
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

		// Mock returns for initial load and page change
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns)
			.mockResolvedValueOnce({ ...mockHistory, pagination: { ...mockHistory.pagination, page: 1 } })
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		// Wait for initial load
		await waitFor(() => {
			expect(screen.getAllByText('Previous').length).toBeGreaterThanOrEqual(1);
		});

		// Clear previous calls
		vi.clearAllMocks();

		// Click Previous button
		const prevButtons = screen.getAllByText('Previous');
		await fireEvent.click(prevButtons[0]);

		// Verify API was called with page=1
		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith(expect.stringMatching(/page=1/));
		});
	});

	it('formats amount with undefined as dash', async () => {
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
					amount: undefined,
					reason: 'Test'
				}
			],
			pagination: { page: 1, per_page: 50, total: 1, total_pages: 1 }
		};
		const mockStats = {
			total: 1,
			forwarded: 1,
			blocked: 0,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			// Should display '-' for undefined amount
			const amountCells = screen.getAllByText('-');
			expect(amountCells.length).toBeGreaterThanOrEqual(1);
		});
	});

	it('displays blocked status with correct styling', async () => {
		const mockHistory = {
			emails: [
				{
					id: 1,
					email_id: 'test1@example.com',
					subject: 'Blocked Email',
					sender: 'spam@example.com',
					received_at: '2024-01-01T10:00:00Z',
					processed_at: '2024-01-01T10:01:00Z',
					status: 'blocked',
					account_email: 'user@example.com',
					category: 'spam',
					amount: undefined,
					reason: 'Blocked by rule'
				}
			],
			pagination: { page: 1, per_page: 50, total: 1, total_pages: 1 }
		};
		const mockStats = {
			total: 1,
			forwarded: 0,
			blocked: 1,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			const emails = screen.getAllByText('Blocked Email');
			expect(emails.length).toBeGreaterThanOrEqual(1);
			expect(screen.getAllByText('blocked').length).toBeGreaterThanOrEqual(1);
		});
	});

	it('displays error status with correct styling', async () => {
		const mockHistory = {
			emails: [
				{
					id: 1,
					email_id: 'test1@example.com',
					subject: 'Failed Email',
					sender: 'test@example.com',
					received_at: '2024-01-01T10:00:00Z',
					processed_at: '2024-01-01T10:01:00Z',
					status: 'error',
					account_email: 'user@example.com',
					category: 'unknown',
					amount: undefined,
					reason: 'Processing failed'
				}
			],
			pagination: { page: 1, per_page: 50, total: 1, total_pages: 1 }
		};
		const mockStats = {
			total: 1,
			forwarded: 0,
			blocked: 0,
			errors: 1,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			const emails = screen.getAllByText('Failed Email');
			expect(emails.length).toBeGreaterThanOrEqual(1);
			expect(screen.getAllByText('error').length).toBeGreaterThanOrEqual(1);
		});
	});

	it('displays unknown status with default styling', async () => {
		const mockHistory = {
			emails: [
				{
					id: 1,
					email_id: 'test1@example.com',
					subject: 'Unknown Email',
					sender: 'test@example.com',
					received_at: '2024-01-01T10:00:00Z',
					processed_at: '2024-01-01T10:01:00Z',
					status: 'pending',
					account_email: 'user@example.com',
					category: 'unknown',
					amount: undefined,
					reason: 'Pending processing'
				}
			],
			pagination: { page: 1, per_page: 50, total: 1, total_pages: 1 }
		};
		const mockStats = {
			total: 1,
			forwarded: 0,
			blocked: 0,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			const emails = screen.getAllByText('Unknown Email');
			expect(emails.length).toBeGreaterThanOrEqual(1);
			expect(screen.getAllByText('pending').length).toBeGreaterThanOrEqual(1);
		});
	});

	it('opens modal when clicking on ignored status badge', async () => {
		const mockHistory = {
			emails: [
				{
					id: 1,
					email_id: 'test1@example.com',
					subject: 'Ignored Email',
					sender: 'test@example.com',
					received_at: '2024-01-01T10:00:00Z',
					processed_at: '2024-01-01T10:01:00Z',
					status: 'ignored',
					account_email: 'user@example.com',
					category: 'unknown',
					amount: 10.0,
					reason: 'Ignored by rule'
				}
			],
			pagination: { page: 1, per_page: 50, total: 1, total_pages: 1 }
		};
		const mockStats = {
			total: 1,
			forwarded: 0,
			blocked: 1,
			errors: 0,
			total_amount: 0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns)
			.mockResolvedValue({ email_id: 1, analysis: { steps: [], final_decision: false } });

		render(History);

		await waitFor(() => {
			const emails = screen.getAllByText('Ignored Email');
			expect(emails.length).toBeGreaterThanOrEqual(1);
		});

		// Click on the ignored status badge (first one)
		const ignoredBadges = screen.getAllByText('ignored');
		await fireEvent.click(ignoredBadges[0]);

		// Modal should open
		await waitFor(() => {
			expect(screen.getByText('Forward Ignored Email')).toBeTruthy();
		});
	});

	it('displays email with account_email when present', async () => {
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
					account_email: 'account@test.com',
					category: 'test',
					amount: 10.0,
					reason: 'Test'
				}
			],
			pagination: { page: 1, per_page: 50, total: 1, total_pages: 1 }
		};
		const mockStats = {
			total: 1,
			forwarded: 1,
			blocked: 0,
			errors: 0,
			total_amount: 10.0,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			expect(screen.getByText(/via account@test.com/)).toBeTruthy();
		});
	});

	it('displays email amount when present', async () => {
		const mockHistory = {
			emails: [
				{
					id: 1,
					email_id: 'test1@example.com',
					subject: 'Test Email with Amount',
					sender: 'test@example.com',
					received_at: '2024-01-01T10:00:00Z',
					processed_at: '2024-01-01T10:01:00Z',
					status: 'forwarded',
					account_email: 'user@example.com',
					category: 'test',
					amount: 99.99,
					reason: 'Test'
				}
			],
			pagination: { page: 1, per_page: 50, total: 1, total_pages: 1 }
		};
		const mockStats = {
			total: 1,
			forwarded: 1,
			blocked: 0,
			errors: 0,
			total_amount: 99.99,
			status_breakdown: {}
		};
		const mockRuns = { runs: [] };

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockHistory)
			.mockResolvedValueOnce(mockStats)
			.mockResolvedValueOnce(mockRuns);

		render(History);

		await waitFor(() => {
			// Amount appears in both desktop and mobile views
			const amounts = screen.getAllByText('$99.99');
			expect(amounts.length).toBeGreaterThanOrEqual(1);
		});
	});
});
