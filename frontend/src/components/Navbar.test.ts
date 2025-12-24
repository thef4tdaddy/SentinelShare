import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import Navbar from './Navbar.svelte';

describe('Navbar Component', () => {
	it('renders the app title', () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		expect(screen.getByAltText('SentinelShare Logo')).toBeTruthy();
	});

	it('renders dashboard and settings buttons', () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		expect(screen.getAllByText('Dashboard').length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText('Settings').length).toBeGreaterThanOrEqual(1);
	});

	it('highlights active view button', () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		const dashboardButton = screen.getAllByText('Dashboard')[0].closest('button');
		expect(
			dashboardButton?.classList.contains('bg-white') ||
				dashboardButton?.classList.contains('bg-primary/5')
		).toBe(true);
	});

	it('highlights settings button when active', () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'settings', onViewChange });
		const settingsButton = screen.getAllByText('Settings')[0].closest('button');
		expect(
			settingsButton?.classList.contains('bg-white') ||
				settingsButton?.classList.contains('bg-primary/5')
		).toBe(true);

		// Verify dashboard is NOT active
		const dashboardButton = screen.getAllByText('Dashboard')[0].closest('button');
		expect(dashboardButton?.classList.contains('bg-white')).toBe(false);
	});

	it('calls onViewChange when dashboard button is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'settings', onViewChange });
		const dashboardButton = screen.getAllByText('Dashboard')[0];
		await fireEvent.click(dashboardButton);
		expect(onViewChange).toHaveBeenCalledWith('dashboard');
	});

	it('calls onViewChange when settings button is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		const settingsButton = screen.getAllByText('Settings')[0];
		await fireEvent.click(settingsButton);
		expect(onViewChange).toHaveBeenCalledWith('settings');
	});
});
