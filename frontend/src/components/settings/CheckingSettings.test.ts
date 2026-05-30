import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CheckingSettings from './CheckingSettings.svelte';
import * as api from '../../lib/api';
import { toasts } from '../../lib/stores/toast';

// Mock api and toast stores
vi.mock('../../lib/api', () => ({
	fetchJson: vi.fn()
}));

vi.mock('../../lib/stores/toast', () => ({
	toasts: {
		trigger: vi.fn(),
		subscribe: vi.fn(() => () => {}),
		remove: vi.fn()
	}
}));

describe('CheckingSettings Component', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('renders checking settings with Active status initially', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue({ disabled: false });
		render(CheckingSettings);

		await waitFor(() => {
			expect(screen.getByText('Email Checking Status')).toBeTruthy();
			expect(screen.getByText('Active')).toBeTruthy();
			expect(screen.getByText(/actively monitoring and processing/)).toBeTruthy();
			expect(screen.getByText('Disable Checking')).toBeTruthy();
		});
	});

	it('renders checking settings with Disabled status when fetched', async () => {
		vi.mocked(api.fetchJson).mockResolvedValue({ disabled: true });
		render(CheckingSettings);

		await waitFor(() => {
			expect(screen.getByText('Disabled')).toBeTruthy();
			expect(screen.getByText(/currently paused/)).toBeTruthy();
			expect(screen.getByText('Enable Checking')).toBeTruthy();
		});
	});

	it('toggles checking status on button click', async () => {
		vi.mocked(api.fetchJson)
			.mockResolvedValueOnce({ disabled: false }) // initial load
			.mockResolvedValueOnce({ disabled: true }); // post response

		render(CheckingSettings);

		await waitFor(() => {
			expect(screen.getByText('Active')).toBeTruthy();
		});

		const btn = screen.getByLabelText('Toggle email checking');
		await fireEvent.click(btn);

		await waitFor(() => {
			expect(api.fetchJson).toHaveBeenLastCalledWith('/settings/disable-checking', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ disabled: true })
			});
			expect(toasts.trigger).toHaveBeenCalledWith('Email checking disabled globally', 'success');
		});
	});
});
