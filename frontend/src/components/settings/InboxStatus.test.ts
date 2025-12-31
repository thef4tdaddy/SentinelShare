// No external lib imports here, but let's check
import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import InboxStatus from './InboxStatus.svelte';

describe('InboxStatus Component', () => {
	it('renders empty state when no results provided', () => {
		render(InboxStatus, { results: [] });
		expect(screen.getByText('Inbox Status')).toBeTruthy();
		expect(screen.getByText('No accounts configured or check pending...')).toBeTruthy();
	});

	it('renders connected accounts correctly', () => {
		const results = [{ account: 'test@example.com', success: true }];
		render(InboxStatus, { results });
		expect(screen.getByText('test@example.com')).toBeTruthy();
		expect(screen.getByText('Connected')).toBeTruthy();
	});

	it('renders failed accounts correctly', () => {
		const results = [{ account: 'fail@example.com', success: false, error: 'Auth failed' }];
		render(InboxStatus, { results });
		expect(screen.getByText('fail@example.com')).toBeTruthy();
		expect(screen.getByText('Connection Failed')).toBeTruthy();
		expect(screen.getByText('Auth failed')).toBeTruthy();
	});
});
