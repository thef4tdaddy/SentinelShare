import { render, screen, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach, beforeAll } from 'vitest';
import Toast from './Toast.svelte';
import { toasts } from '../lib/stores/toast';
import { get } from 'svelte/store';
import { tick } from 'svelte';

// Mock the animate function and getAnimations for transitions to avoid jsdom errors
beforeAll(() => {
	Element.prototype.animate = vi.fn(() => ({
		finished: Promise.resolve(),
		cancel: vi.fn(),
		onfinish: null,
		oncancel: null,
		play: vi.fn(),
		pause: vi.fn(),
		reverse: vi.fn(),
		finish: vi.fn(),
		updatePlaybackRate: vi.fn(),
		persist: vi.fn(),
		commitStyles: vi.fn(),
		playbackRate: 1,
		playState: 'finished',
		ready: Promise.resolve(),
		pending: false,
		id: '',
		startTime: 0,
		currentTime: 0,
		timeline: null,
		effect: null
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
	})) as any;

	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	Element.prototype.getAnimations = vi.fn(() => []) as any;
});

describe('Toast Component', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	afterEach(() => {
		// Clean up toasts after each test
		const currentToasts = get(toasts);
		currentToasts.forEach((toast) => toasts.remove(toast.id));
	});

	it('renders without toasts initially', () => {
		const { container } = render(Toast);
		const toastContainer = container.querySelector('.fixed.bottom-4.right-4');
		expect(toastContainer).toBeTruthy();
		expect(toastContainer?.children.length).toBe(0);
	});

	it('renders a success toast with correct theme', async () => {
		render(Toast);

		toasts.trigger('Success message', 'success', 0);

		await tick();
		await waitFor(() => {
			expect(screen.getByText('Success message')).toBeTruthy();
		});

		const toastElement = screen.getByText('Success message').closest('div');
		expect(toastElement?.className).toContain('bg-emerald-50');
		expect(toastElement?.className).toContain('border-emerald-100');

		// Verify icon is present
		const icon = toastElement?.querySelector('svg');
		expect(icon).toBeTruthy();
	});

	it('renders an error toast with correct theme', async () => {
		render(Toast);

		toasts.trigger('Error message', 'error', 0);

		await tick();
		await waitFor(() => {
			expect(screen.getByText('Error message')).toBeTruthy();
		});

		const toastElement = screen.getByText('Error message').closest('div');
		expect(toastElement?.className).toContain('bg-red-50');
		expect(toastElement?.className).toContain('border-red-100');

		// Verify icon is present
		const icon = toastElement?.querySelector('svg');
		expect(icon).toBeTruthy();
	});

	it('renders an info toast with correct theme', async () => {
		render(Toast);

		toasts.trigger('Info message', 'info', 0);

		await tick();
		await waitFor(() => {
			expect(screen.getByText('Info message')).toBeTruthy();
		});

		const toastElement = screen.getByText('Info message').closest('div');
		expect(toastElement?.className).toContain('bg-blue-50');
		expect(toastElement?.className).toContain('border-blue-100');

		// Verify icon is present
		const icon = toastElement?.querySelector('svg');
		expect(icon).toBeTruthy();
	});

	it('renders multiple toasts at once', async () => {
		render(Toast);

		toasts.trigger('First toast', 'info', 0);
		await tick();
		toasts.trigger('Second toast', 'success', 0);
		await tick();
		toasts.trigger('Third toast', 'error', 0);
		await tick();

		await waitFor(
			() => {
				expect(screen.getAllByLabelText('Close notification').length).toBe(3);
			},
			{ timeout: 1000 }
		);
	});

	it('renders close button with correct aria-label', async () => {
		render(Toast);

		toasts.trigger('Test message', 'info', 0);

		await tick();

		await waitFor(() => {
			const closeButton = screen.getByLabelText('Close notification');
			expect(closeButton).toBeTruthy();
			expect(closeButton.tagName).toBe('BUTTON');
		});
	});

	it.skip('auto-removes toast after specified duration', async () => {
		vi.useFakeTimers();
		render(Toast);

		toasts.trigger('Auto dismiss', 'info', 1000);

		await tick();

		await waitFor(() => {
			expect(screen.getByText('Auto dismiss')).toBeTruthy();
		});

		// Fast-forward time (1000ms for timeout + 200ms for transition)
		vi.advanceTimersByTime(1200);
		await tick();

		await waitFor(() => {
			expect(screen.queryByText('Auto dismiss')).toBeNull();
		});

		vi.useRealTimers();
	});

	it('does not auto-remove toast when duration is 0', async () => {
		vi.useFakeTimers();
		render(Toast);

		toasts.trigger('No auto dismiss', 'info', 0);

		await tick();

		await waitFor(() => {
			expect(screen.getByText('No auto dismiss')).toBeTruthy();
		});

		// Fast-forward time
		vi.advanceTimersByTime(5000);
		await tick();

		// Should still be visible
		expect(screen.getByText('No auto dismiss')).toBeTruthy();

		vi.useRealTimers();
	});

	it('applies correct container and positioning classes', () => {
		const { container } = render(Toast);
		const toastContainer = container.querySelector('.fixed.bottom-4.right-4');
		expect(toastContainer).toBeTruthy();
		expect(toastContainer?.className).toContain('z-[100]');
		expect(toastContainer?.className).toContain('flex-col');
		expect(toastContainer?.className).toContain('gap-2');
		expect(toastContainer?.className).toContain('pointer-events-none');
	});

	it('applies pointer-events-auto to individual toasts', async () => {
		render(Toast);

		toasts.trigger('Test', 'info', 0);

		await tick();

		await waitFor(() => {
			const toastElement = screen.getByText('Test').closest('div');
			expect(toastElement?.className).toContain('pointer-events-auto');
		});
	});

	it('applies correct styling classes to toast container', async () => {
		render(Toast);

		toasts.trigger('Test', 'info', 0);

		await tick();

		await waitFor(() => {
			const toastElement = screen.getByText('Test').closest('div');
			expect(toastElement?.className).toContain('rounded-xl');
			expect(toastElement?.className).toContain('shadow-lg');
			expect(toastElement?.className).toContain('border');
			expect(toastElement?.className).toContain('backdrop-blur-xl');
			expect(toastElement?.className).toContain('min-w-[300px]');
			expect(toastElement?.className).toContain('max-w-sm');
		});
	});

	it('renders X icon in close button', async () => {
		render(Toast);

		toasts.trigger('Test', 'info', 0);

		await tick();

		await waitFor(() => {
			const closeButton = screen.getByLabelText('Close notification');
			const xIcon = closeButton.querySelector('svg');
			expect(xIcon).toBeTruthy();
		});
	});

	it('applies hover styles to close button', async () => {
		render(Toast);

		toasts.trigger('Test', 'info', 0);

		await tick();

		await waitFor(() => {
			const closeButton = screen.getByLabelText('Close notification');
			expect(closeButton.className).toContain('hover:bg-black/5');
			expect(closeButton.className).toContain('rounded-lg');
			expect(closeButton.className).toContain('transition-colors');
		});
	});

	it('applies text styling classes correctly', async () => {
		render(Toast);

		toasts.trigger('Test message', 'info', 0);

		await tick();

		await waitFor(() => {
			const messageElement = screen.getByText('Test message');
			expect(messageElement.className).toContain('text-sm');
			expect(messageElement.className).toContain('font-medium');
			expect(messageElement.className).toContain('flex-1');
			expect(messageElement.className).toContain('leading-snug');
		});
	});

	it('uses unique ids for each toast', async () => {
		const nowSpy = vi.spyOn(Date, 'now');
		let mockTime = 1_000;
		nowSpy.mockImplementation(() => mockTime++);

		try {
			render(Toast);

			toasts.trigger('Toast 1', 'info', 0);
			toasts.trigger('Toast 2', 'info', 0);

			await tick();

			await waitFor(() => {
				const updatedToasts = get(toasts);
				expect(updatedToasts.length).toBeGreaterThanOrEqual(2);

				// Ensure IDs are different
				if (updatedToasts.length >= 2) {
					const lastTwo = updatedToasts.slice(-2);
					expect(lastTwo[0].id).not.toBe(lastTwo[1].id);
				}
			});
		} finally {
			nowSpy.mockRestore();
		}
	});

	it('handles empty message gracefully', async () => {
		render(Toast);

		toasts.trigger('', 'info', 0);

		await tick();

		// Should render with empty text
		await waitFor(() => {
			const toastElements = screen.queryAllByLabelText('Close notification');
			expect(toastElements.length).toBe(1);
		});
	});

	it('applies shrink-0 class to icon container', async () => {
		render(Toast);

		toasts.trigger('Test', 'info', 0);

		await tick();

		await waitFor(() => {
			const toastElement = screen.getByText('Test').closest('div');
			const iconContainer = toastElement?.querySelector('.shrink-0');
			expect(iconContainer).toBeTruthy();
		});
	});
});
