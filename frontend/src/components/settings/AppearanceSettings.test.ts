import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import AppearanceSettings from './AppearanceSettings.svelte';
import { theme } from '../../lib/stores/theme';

// Mock the theme store
vi.mock('../../lib/stores/theme', () => {
	// Create a simple mock store structure
	const mockSubscribe = vi.fn((run) => {
		run('light'); // Initial value
		return () => {};
	});

	return {
		theme: {
			subscribe: mockSubscribe,
			toggle: vi.fn()
		}
	};
});

describe('AppearanceSettings Component', () => {
	it('renders appearance settings', () => {
		render(AppearanceSettings);
		expect(screen.getByText('Appearance')).toBeTruthy();
		expect(screen.getByText('Dark Mode')).toBeTruthy();
		expect(screen.getByText('Toggle between light and dark theme')).toBeTruthy();
	});

	it('calls toggle on button click', async () => {
		render(AppearanceSettings);
		const btn = screen.getByLabelText('Toggle theme');
		await fireEvent.click(btn);
		expect(theme.toggle).toHaveBeenCalled();
	});
});
