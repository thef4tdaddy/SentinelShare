import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SuggestedRules from './SuggestedRules.svelte';
import { api } from '../lib/api';
import { toasts } from '../lib/stores/toast';

// Mock the API
vi.mock('../lib/api', () => ({
	api: {
		learning: {
			scan: vi.fn(),
			getCandidates: vi.fn(),
			approve: vi.fn(),
			ignore: vi.fn()
		}
	}
}));

// Mock the toast store
vi.mock('../lib/stores/toast', () => ({
	toasts: {
		trigger: vi.fn(),
		subscribe: vi.fn(() => () => {}),
		remove: vi.fn()
	}
}));

describe('SuggestedRules Component', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	const mockCandidates = [
		{
			id: 1,
			sender: 'receipts@store.com',
			subject_pattern: '*Order*',
			confidence: 0.8,
			type: 'Receipt',
			matches: 2,
			created_at: new Date().toISOString()
		}
	];

	it('renders loading state initially', () => {
		vi.mocked(api.learning.getCandidates).mockReturnValue(new Promise(() => {})); // Never resolves
		render(SuggestedRules, { onRuleAdded: vi.fn() });
		expect(screen.getByText('Discovering matching patterns...')).toBeTruthy();
	});

	it('renders empty state when no candidates', async () => {
		vi.mocked(api.learning.getCandidates).mockResolvedValue([]);
		render(SuggestedRules, { onRuleAdded: vi.fn() });

		await waitFor(() => {
			expect(
				screen.getByText('No suggestions found. Try scanning your history for missed receipts.')
			).toBeTruthy();
		});
	});

	it('renders candidates list', async () => {
		vi.mocked(api.learning.getCandidates).mockResolvedValue(mockCandidates);
		render(SuggestedRules, { onRuleAdded: vi.fn() });

		await waitFor(() => {
			expect(screen.getByText('receipts@store.com')).toBeTruthy();
			expect(screen.getByText('*Order*')).toBeTruthy();
		});
	});

	it('calls scan API when scan button clicked', async () => {
		vi.mocked(api.learning.getCandidates).mockResolvedValue(mockCandidates);
		render(SuggestedRules, { onRuleAdded: vi.fn() });

		const scanButton = screen.getByText('Scan for Missed');
		await fireEvent.click(scanButton);

		expect(api.learning.scan).toHaveBeenCalledWith(30);
	});

	it('calls approve API and callback when approve clicked', async () => {
		vi.mocked(api.learning.getCandidates).mockResolvedValue(mockCandidates);
		const mockOnAdd = vi.fn();
		render(SuggestedRules, { onRuleAdded: mockOnAdd });

		await waitFor(() => screen.getByText('Add Rule'));

		const approveBtn = screen.getByText('Add Rule');
		await fireEvent.click(approveBtn);

		expect(api.learning.approve).toHaveBeenCalledWith(1);
		await waitFor(() => {
			expect(mockOnAdd).toHaveBeenCalled();
		});
	});

	it('calls ignore API when ignore clicked', async () => {
		vi.mocked(api.learning.getCandidates).mockResolvedValue(mockCandidates);
		render(SuggestedRules, { onRuleAdded: vi.fn() });

		await waitFor(() => screen.getByText('Ignore'));

		const ignoreBtn = screen.getByText('Ignore');
		await fireEvent.click(ignoreBtn);

		expect(api.learning.ignore).toHaveBeenCalledWith(1);
	});

	it('handles loadCandidates error gracefully', async () => {
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
		vi.mocked(api.learning.getCandidates).mockRejectedValue(new Error('Network error'));
		
		render(SuggestedRules, { onRuleAdded: vi.fn() });

		await waitFor(() => {
			expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to load suggestions', expect.any(Error));
			expect(
				screen.getByText('No suggestions found. Try scanning your history for missed receipts.')
			).toBeTruthy();
		});

		consoleErrorSpy.mockRestore();
	});

	it('handles runScan error gracefully', async () => {
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
		vi.mocked(api.learning.getCandidates).mockResolvedValue(mockCandidates);
		vi.mocked(api.learning.scan).mockRejectedValue(new Error('Scan failed'));
		
		render(SuggestedRules, { onRuleAdded: vi.fn() });

		await waitFor(() => screen.getByText('Scan for Missed'));
		
		const scanButton = screen.getByText('Scan for Missed');
		await fireEvent.click(scanButton);

		await waitFor(() => {
			expect(consoleErrorSpy).toHaveBeenCalledWith('Scan trigger failed', expect.any(Error));
		});

		consoleErrorSpy.mockRestore();
	});

	it('shows success toast when rule is approved', async () => {
		vi.mocked(api.learning.getCandidates).mockResolvedValue(mockCandidates);
		vi.mocked(api.learning.approve).mockResolvedValue(undefined);
		const mockOnAdd = vi.fn();
		
		render(SuggestedRules, { onRuleAdded: mockOnAdd });

		await waitFor(() => screen.getByText('Add Rule'));

		const approveBtn = screen.getByText('Add Rule');
		await fireEvent.click(approveBtn);

		await waitFor(() => {
			expect(mockOnAdd).toHaveBeenCalled();
			expect(toasts.trigger).toHaveBeenCalledWith('Rule created successfully', 'success');
		});
	});

	it('removes candidate from list after successful ignore', async () => {
		vi.mocked(api.learning.getCandidates).mockResolvedValue(mockCandidates);
		vi.mocked(api.learning.ignore).mockResolvedValue(undefined);
		
		render(SuggestedRules, { onRuleAdded: vi.fn() });

		await waitFor(() => screen.getByText('Ignore'));

		const ignoreBtn = screen.getByText('Ignore');
		await fireEvent.click(ignoreBtn);

		await waitFor(() => {
			expect(api.learning.ignore).toHaveBeenCalledWith(1);
			// After ignoring, the candidate should be removed from the list
			expect(
				screen.queryByText('No suggestions found. Try scanning your history for missed receipts.')
			).toBeTruthy();
		});
	});

	it('renders example_subject when present', async () => {
		const candidatesWithExample = [
			{
				id: 1,
				sender: 'receipts@store.com',
				subject_pattern: '*Order*',
				confidence: 0.8,
				type: 'Receipt',
				matches: 2,
				example_subject: 'Your Order #12345 has been shipped',
				created_at: new Date().toISOString()
			}
		];
		
		vi.mocked(api.learning.getCandidates).mockResolvedValue(candidatesWithExample);
		render(SuggestedRules, { onRuleAdded: vi.fn() });

		await waitFor(() => {
			expect(screen.getByText(/Your Order #12345 has been shipped/)).toBeTruthy();
		});
	});

	it('handles approve error gracefully', async () => {
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
		vi.mocked(api.learning.getCandidates).mockResolvedValue(mockCandidates);
		vi.mocked(api.learning.approve).mockRejectedValue(new Error('Approval failed'));
		
		render(SuggestedRules, { onRuleAdded: vi.fn() });

		await waitFor(() => screen.getByText('Add Rule'));

		const approveBtn = screen.getByText('Add Rule');
		await fireEvent.click(approveBtn);

		await waitFor(() => {
			expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to approve', expect.any(Error));
			expect(toasts.trigger).toHaveBeenCalledWith('Failed to create rule', 'error');
		});

		consoleErrorSpy.mockRestore();
	});

	it('handles ignore error gracefully', async () => {
		const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
		vi.mocked(api.learning.getCandidates).mockResolvedValue(mockCandidates);
		vi.mocked(api.learning.ignore).mockRejectedValue(new Error('Ignore failed'));
		
		render(SuggestedRules, { onRuleAdded: vi.fn() });

		await waitFor(() => screen.getByText('Ignore'));

		const ignoreBtn = screen.getByText('Ignore');
		await fireEvent.click(ignoreBtn);

		await waitFor(() => {
			expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to ignore', expect.any(Error));
		});

		consoleErrorSpy.mockRestore();
	});
});
