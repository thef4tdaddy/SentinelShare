import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import SuggestedRules from './SuggestedRules.svelte';
import { api } from '../lib/api';

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

describe('SuggestedRules Component', () => {
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
		expect(screen.getByText('Loading suggestions...')).toBeTruthy();
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
});
