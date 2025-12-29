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

	it('calls onViewChange when logo is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'settings', onViewChange });
		const logo = screen.getByAltText('SentinelShare Logo');
		const logoButton = logo.closest('button');
		expect(logoButton).toBeTruthy();
		await fireEvent.click(logoButton!);
		expect(onViewChange).toHaveBeenCalledWith('dashboard');
	});

	it('calls onViewChange when history button is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		const historyButton = screen.getAllByText('History')[0];
		await fireEvent.click(historyButton);
		expect(onViewChange).toHaveBeenCalledWith('history');
	});

	it('calls onViewChange when rules button is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		const rulesButton = screen.getAllByText('Rules')[0];
		await fireEvent.click(rulesButton);
		expect(onViewChange).toHaveBeenCalledWith('rules');
	});

	it('calls onViewChange when preferences button is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		const preferencesButton = screen.getAllByText(/^Preferences$|^Prefs$/)[0];
		await fireEvent.click(preferencesButton);
		expect(onViewChange).toHaveBeenCalledWith('preferences');
	});

	// Mobile navigation tests
	it('renders mobile navigation buttons', () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		// Mobile navigation should have Home, History, Rules, Prefs, Settings
		expect(screen.getByText('Home')).toBeTruthy();
		expect(screen.getByText('Prefs')).toBeTruthy();
	});

	it('calls onViewChange when mobile dashboard button is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'settings', onViewChange });
		const mobileHomeButton = screen.getByText('Home');
		await fireEvent.click(mobileHomeButton);
		expect(onViewChange).toHaveBeenCalledWith('dashboard');
	});

	it('calls onViewChange when mobile history button is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		// Get all History text elements, find the one with "History" (mobile has same text)
		const historyButtons = screen.getAllByText('History');
		// Click the last one (mobile version)
		await fireEvent.click(historyButtons[historyButtons.length - 1]);
		expect(onViewChange).toHaveBeenCalledWith('history');
	});

	it('calls onViewChange when mobile rules button is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		const rulesButtons = screen.getAllByText('Rules');
		// Click the last one (mobile version)
		await fireEvent.click(rulesButtons[rulesButtons.length - 1]);
		expect(onViewChange).toHaveBeenCalledWith('rules');
	});

	it('calls onViewChange when mobile preferences button is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		const mobilePrefsButton = screen.getByText('Prefs');
		await fireEvent.click(mobilePrefsButton);
		expect(onViewChange).toHaveBeenCalledWith('preferences');
	});

	it('calls onViewChange when mobile settings button is clicked', async () => {
		const onViewChange = vi.fn();
		render(Navbar, { currentView: 'dashboard', onViewChange });
		const settingsButtons = screen.getAllByText('Settings');
		// Click the last one (mobile version)
		await fireEvent.click(settingsButtons[settingsButtons.length - 1]);
		expect(onViewChange).toHaveBeenCalledWith('settings');
	});
});
