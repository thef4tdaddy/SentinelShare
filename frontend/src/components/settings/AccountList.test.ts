import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import AccountList from './AccountList.svelte';
import { fetchJson } from '../../lib/api';

// Mock dependencies
vi.mock('../../lib/api', () => ({
	fetchJson: vi.fn()
}));

vi.mock('../../lib/stores/toast', () => ({
	toasts: {
		trigger: vi.fn()
	}
}));

describe('AccountList Component', () => {
	it('renders empty state correctly', async () => {
		vi.mocked(fetchJson).mockResolvedValueOnce([]);
		render(AccountList);
		expect(screen.getByText('Email Accounts')).toBeTruthy();
		// Wait for loading to finish if necessary, but initial render usually shows something
	});

	it('renders Add Account button', () => {
		vi.mocked(fetchJson).mockResolvedValueOnce([]);
		render(AccountList);
		expect(screen.getByText('Add Account')).toBeTruthy();
	});
});
