import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import Navbar from './Navbar.svelte';

describe('Navbar Component', () => {
	it('renders the app title', () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		expect(screen.getByAltText('SentinelShare')).toBeTruthy();
	});

	it('renders dashboard and settings buttons', () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		expect(screen.getByText('Dashboard')).toBeTruthy();
		expect(screen.getByText('Settings')).toBeTruthy();
	});

	it('highlights active view button', () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		const dashboardButton = screen.getByText('Dashboard').closest('button');
		expect(dashboardButton?.classList.contains('bg-white')).toBe(true);
		expect(dashboardButton?.classList.contains('text-primary')).toBe(true);
	});

	it('highlights settings button when active', () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'settings', onViewChange });
		const settingsButton = screen.getByText('Settings').closest('button');
		expect(settingsButton?.classList.contains('bg-white')).toBe(true);
		expect(settingsButton?.classList.contains('text-primary')).toBe(true);

		// Verify dashboard is NOT active
		const dashboardButton = screen.getByText('Dashboard').closest('button');
		expect(dashboardButton?.classList.contains('bg-white')).toBe(false);
	});

	it('calls onViewChange when dashboard button is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'settings', onViewChange });
		const dashboardButton = screen.getByText('Dashboard');
		await fireEvent.click(dashboardButton);
		expect(onViewChange).toHaveBeenCalledWith('dashboard');
	});

	it('calls onViewChange when settings button is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		const settingsButton = screen.getByText('Settings');
		await fireEvent.click(settingsButton);
		expect(onViewChange).toHaveBeenCalledWith('settings');
	});
});
