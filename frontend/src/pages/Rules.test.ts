import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import Rules from './Rules.svelte';
import * as api from '../lib/api';

// Mock the api module
vi.mock('../lib/api', () => ({
	fetchJson: vi.fn(),
	api: {
		learning: {
			scan: vi.fn(),
			getCandidates: vi.fn().mockResolvedValue([]),
			approve: vi.fn(),
			ignore: vi.fn()
		}
	}
}));

describe('Rules Component', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		window.confirm = vi.fn();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('renders page title and description', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('Automation Rules')).toBeTruthy();
			expect(
				screen.getByText('Manage automated detection rules, adaptive learning, and shadow mode candidates.')
			).toBeTruthy();
		});
	});

	it('shows loading indicator while fetching rules', () => {
		vi.mocked(api.fetchJson).mockReturnValue(new Promise(() => {})); // Never resolves
		render(Rules);

		expect(screen.getByText(/Automation Rules \(Loading\.\.\.\)/i)).toBeTruthy();
	});

	it('renders info cards for adaptive learning features', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('Adaptive Learning')).toBeTruthy();
			expect(screen.getByText('Auto-Apply')).toBeTruthy();
			expect(screen.getByText('Shadow Stats')).toBeTruthy();
		});
	});

	it('displays adaptive learning card content', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);
		render(Rules);

		await waitFor(() => {
			expect(
				screen.getByText('System is currently monitoring feedback and suggesting new rules in Shadow Mode.')
			).toBeTruthy();
			expect(screen.getByText('SHADOW MODE ACTIVE')).toBeTruthy();
		});
	});

	it('displays auto-apply card content', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);
		render(Rules);

		await waitFor(() => {
			expect(
				screen.getByText('Rules with >90% confidence and 3+ successful shadow matches are auto-promoted.')
			).toBeTruthy();
			expect(screen.getByText('Confidence Threshold: 90%')).toBeTruthy();
		});
	});

	it('displays shadow stats with no rules', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('Candidates:')).toBeTruthy();
			expect(screen.getByText('Auto-Applied:')).toBeTruthy();
		});
	});

	it('calculates shadow candidates count correctly', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: true,
				match_count: 5
			},
			{
				id: 2,
				email_pattern: 'another@example.com',
				priority: 2,
				confidence: 0.95,
				is_shadow_mode: true,
				match_count: 3
			},
			{
				id: 3,
				email_pattern: 'active@example.com',
				priority: 3,
				confidence: 0.90,
				is_shadow_mode: false,
				match_count: 10
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			const candidatesElements = screen.getAllByText('2');
			expect(candidatesElements.length).toBeGreaterThan(0);
		});
	});

	it('calculates auto-applied count correctly', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				purpose: 'Auto-detected (AUTO)',
				priority: 1,
				confidence: 0.95,
				is_shadow_mode: false,
				match_count: 8
			},
			{
				id: 2,
				email_pattern: 'manual@example.com',
				purpose: 'Manual rule',
				priority: 2,
				confidence: 0.90,
				is_shadow_mode: false,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			const autoAppliedElements = screen.getAllByText('1');
			expect(autoAppliedElements.length).toBeGreaterThan(0);
		});
	});

	it('renders rules table with headers', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('Type')).toBeTruthy();
			expect(screen.getByText('Pattern')).toBeTruthy();
			expect(screen.getByText('Confidence')).toBeTruthy();
			expect(screen.getByText('Matches')).toBeTruthy();
			expect(screen.getByText('Actions')).toBeTruthy();
		});
	});

	it('renders legend for rule types', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('Manual')).toBeTruthy();
			expect(screen.getByText('Shadow')).toBeTruthy();
			expect(screen.getByText('Auto')).toBeTruthy();
		});
	});

	it('displays rule with email pattern', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'receipts@amazon.com',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: false,
				match_count: 10
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('receipts@amazon.com')).toBeTruthy();
		});
	});

	it('displays rule with subject pattern', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'notifications@store.com',
				subject_pattern: 'Order Confirmation*',
				priority: 1,
				confidence: 0.90,
				is_shadow_mode: false,
				match_count: 15
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('notifications@store.com')).toBeTruthy();
			expect(screen.getByText(/Subject: Order Confirmation\*/)).toBeTruthy();
		});
	});

	it('displays rule purpose description', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				purpose: 'Amazon receipts detection',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: false,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('Amazon receipts detection')).toBeTruthy();
		});
	});

	it('displays "No description" when purpose is missing', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: false,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('No description')).toBeTruthy();
		});
	});

	it('displays "Any Sender" when email_pattern is missing', async () => {
		const mockRules = [
			{
				id: 1,
				subject_pattern: '*Receipt*',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: false,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('Any Sender')).toBeTruthy();
		});
	});

	it('displays SHADOW badge for shadow mode rules', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: true,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('SHADOW')).toBeTruthy();
		});
	});

	it('displays AUTO badge for auto-applied rules', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				purpose: 'Detected automatically (AUTO)',
				priority: 1,
				confidence: 0.95,
				is_shadow_mode: false,
				match_count: 10
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('AUTO')).toBeTruthy();
		});
	});

	it('displays MANUAL badge for manual rules', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				purpose: 'Manual rule',
				priority: 1,
				confidence: 0.90,
				is_shadow_mode: false,
				match_count: 7
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('MANUAL')).toBeTruthy();
		});
	});

	it('displays confidence percentage correctly', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				priority: 1,
				confidence: 0.75,
				is_shadow_mode: false,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('75%')).toBeTruthy();
		});
	});

	it('displays match count', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: false,
				match_count: 42
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('42')).toBeTruthy();
		});
	});

	it('displays multiple rules', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'first@example.com',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: false,
				match_count: 10
			},
			{
				id: 2,
				email_pattern: 'second@example.com',
				priority: 2,
				confidence: 0.90,
				is_shadow_mode: true,
				match_count: 5
			},
			{
				id: 3,
				email_pattern: 'third@example.com',
				purpose: 'Auto (AUTO)',
				priority: 3,
				confidence: 0.95,
				is_shadow_mode: false,
				match_count: 20
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		render(Rules);

		await waitFor(() => {
			expect(screen.getByText('first@example.com')).toBeTruthy();
			expect(screen.getByText('second@example.com')).toBeTruthy();
			expect(screen.getByText('third@example.com')).toBeTruthy();
		});
	});

	it('calls correct API endpoint on mount', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);
		render(Rules);

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith('/settings/rules');
		});
	});

	it('handles API errors gracefully', async () => {
		const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
		vi.mocked(api.fetchJson).mockRejectedValueOnce(new Error('API Error'));

		render(Rules);

		await waitFor(() => {
			expect(consoleSpy).toHaveBeenCalledWith('Failed to load rules', expect.any(Error));
		});

		consoleSpy.mockRestore();
	});

	it('sets loading to false after successful API call', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);
		render(Rules);

		await waitFor(() => {
			// When not loading, the "(Loading...)" text should not be present
			expect(screen.queryByText(/\(Loading\.\.\.\)/)).toBeFalsy();
		});
	});

	it('handles non-array API response gracefully', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue({ error: 'Invalid response' });
		render(Rules);

		await waitFor(() => {
			// Should render table but with no rows since response is not an array
			expect(screen.getByText('Type')).toBeTruthy();
		});
	});

	it('shows confirm dialog when delete button clicked', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: false,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		vi.mocked(window.confirm).mockReturnValue(false);

		render(Rules);

		await waitFor(() => {
			const deleteButtons = screen.getAllByTitle('Delete Rule');
			expect(deleteButtons.length).toBe(1);
		});

		const deleteButton = screen.getByTitle('Delete Rule');
		await fireEvent.click(deleteButton);

		expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete this rule?');
	});

	it('does not delete rule when user cancels confirm dialog', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: false,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		vi.mocked(window.confirm).mockReturnValue(false);

		render(Rules);

		await waitFor(() => {
			expect(screen.getByTitle('Delete Rule')).toBeTruthy();
		});

		vi.clearAllMocks();
		const deleteButton = screen.getByTitle('Delete Rule');
		await fireEvent.click(deleteButton);

		// Should not call the delete API endpoint
		expect(api.fetchJson).not.toHaveBeenCalledWith(
			expect.stringContaining('/settings/manual-rule/'),
			expect.anything()
		);
	});

	it('deletes rule when user confirms', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: false,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockRules) // Initial load
			.mockResolvedValueOnce({}) // Delete response
			.mockResolvedValueOnce([]); // Reload after delete

		vi.mocked(window.confirm).mockReturnValue(true);

		render(Rules);

		await waitFor(() => {
			expect(screen.getByTitle('Delete Rule')).toBeTruthy();
		});

		const deleteButton = screen.getByTitle('Delete Rule');
		await fireEvent.click(deleteButton);

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenCalledWith('/settings/manual-rule/1', { method: 'DELETE' });
		});
	});

	it('reloads rules after successful deletion', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: false,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockRules) // Initial load
			.mockResolvedValueOnce({}) // Delete response
			.mockResolvedValueOnce([]); // Reload after delete

		vi.mocked(window.confirm).mockReturnValue(true);

		render(Rules);

		await waitFor(() => {
			expect(screen.getByTitle('Delete Rule')).toBeTruthy();
		});

		vi.clearAllMocks();
		const deleteButton = screen.getByTitle('Delete Rule');
		await fireEvent.click(deleteButton);

		await waitFor(() => {
			// Verify that loadRules was called again (API called twice: delete + reload)
			expect(api.fetchJson).toHaveBeenCalledTimes(2);
			expect(api.fetchJson).toHaveBeenCalledWith('/settings/rules');
		});
	});

	it('handles delete API errors gracefully', async () => {
		const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				priority: 1,
				confidence: 0.85,
				is_shadow_mode: false,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce(mockRules)
			.mockRejectedValueOnce(new Error('Delete failed'));

		vi.mocked(window.confirm).mockReturnValue(true);

		render(Rules);

		await waitFor(() => {
			expect(screen.getByTitle('Delete Rule')).toBeTruthy();
		});

		const deleteButton = screen.getByTitle('Delete Rule');
		await fireEvent.click(deleteButton);

		await waitFor(() => {
			expect(consoleSpy).toHaveBeenCalledWith('Failed to delete rule', expect.any(Error));
		});

		consoleSpy.mockRestore();
	});

	it('renders SuggestedRules component', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue([]);
		render(Rules);

		await waitFor(() => {
			// Component should be in the DOM (we mocked it, so just verify rendering completed)
			expect(screen.getByText('Active & Suggested Rules')).toBeTruthy();
		});
	});

	it('displays high confidence bar with emerald color', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				priority: 1,
				confidence: 0.95, // > 0.8
				is_shadow_mode: false,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		const { container } = render(Rules);

		await waitFor(() => {
			expect(screen.getByText('95%')).toBeTruthy();
			// Check for emerald color class
			const confidenceBar = container.querySelector('.bg-emerald-500');
			expect(confidenceBar).toBeTruthy();
		});
	});

	it('displays normal confidence bar with indigo color', async () => {
		const mockRules = [
			{
				id: 1,
				email_pattern: 'test@example.com',
				priority: 1,
				confidence: 0.65, // <= 0.8
				is_shadow_mode: false,
				match_count: 5
			}
		];

		vi.mocked(api.fetchJson).mockResolvedValue(mockRules);
		const { container } = render(Rules);

		await waitFor(() => {
			expect(screen.getByText('65%')).toBeTruthy();
			// Check for indigo color class
			const confidenceBar = container.querySelector('.bg-indigo-500');
			expect(confidenceBar).toBeTruthy();
		});
	});
});
