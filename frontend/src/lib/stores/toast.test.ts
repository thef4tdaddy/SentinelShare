import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { get } from 'svelte/store';
import { toasts, type Toast, type ToastType } from './toast';

describe('toast store', () => {
	beforeEach(() => {
		vi.useFakeTimers();
		// Clear all toasts before each test
		const currentToasts = get(toasts);
		currentToasts.forEach((toast) => toasts.remove(toast.id));
	});

	afterEach(() => {
		vi.restoreAllMocks();
		vi.useRealTimers();
	});

	describe('trigger', () => {
		it('adds a toast with default parameters', () => {
			const currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(0);

			toasts.trigger('Test message');

			const updatedToasts = get(toasts);
			expect(updatedToasts).toHaveLength(1);
			expect(updatedToasts[0]).toMatchObject({
				message: 'Test message',
				type: 'info',
				duration: 3000
			});
			expect(updatedToasts[0].id).toBeDefined();
			expect(typeof updatedToasts[0].id).toBe('number');
		});

		it('adds a toast with custom type - success', () => {
			toasts.trigger('Success message', 'success');

			const currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);
			expect(currentToasts[0]).toMatchObject({
				message: 'Success message',
				type: 'success',
				duration: 3000
			});
		});

		it('adds a toast with custom type - error', () => {
			toasts.trigger('Error message', 'error');

			const currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);
			expect(currentToasts[0]).toMatchObject({
				message: 'Error message',
				type: 'error',
				duration: 3000
			});
		});

		it('adds a toast with custom type - info', () => {
			toasts.trigger('Info message', 'info');

			const currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);
			expect(currentToasts[0]).toMatchObject({
				message: 'Info message',
				type: 'info',
				duration: 3000
			});
		});

		it('adds a toast with custom duration', () => {
			toasts.trigger('Custom duration', 'info', 5000);

			const currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);
			expect(currentToasts[0]).toMatchObject({
				message: 'Custom duration',
				type: 'info',
				duration: 5000
			});
		});

		it('adds a toast with zero duration (no auto-dismiss)', () => {
			toasts.trigger('Persistent message', 'info', 0);

			const currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);
			expect(currentToasts[0]).toMatchObject({
				message: 'Persistent message',
				type: 'info',
				duration: 0
			});

			// Advance timers and verify toast is not removed
			vi.advanceTimersByTime(10000);
			const persistentToasts = get(toasts);
			expect(persistentToasts).toHaveLength(1);
		});

		it('generates unique IDs for multiple toasts', () => {
			toasts.trigger('First message', 'info', 0);
			vi.advanceTimersByTime(1);
			toasts.trigger('Second message', 'info', 0);
			vi.advanceTimersByTime(1);
			toasts.trigger('Third message', 'info', 0);

			const currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(3);

			const ids = currentToasts.map((t) => t.id);
			const uniqueIds = new Set(ids);
			expect(uniqueIds.size).toBe(3);
		});

		it('automatically removes toast after duration expires', () => {
			toasts.trigger('Auto remove', 'info', 3000);

			let currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);

			// Advance timer by duration
			vi.advanceTimersByTime(3000);

			currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(0);
		});

		it('automatically removes only expired toasts', () => {
			toasts.trigger('Short lived', 'info', 1000);
			vi.advanceTimersByTime(1);
			toasts.trigger('Long lived', 'success', 5000);

			let currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(2);

			// Advance timer to remove first toast
			vi.advanceTimersByTime(1000);

			currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);
			expect(currentToasts[0].message).toBe('Long lived');

			// Advance timer to remove second toast
			vi.advanceTimersByTime(4000);

			currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(0);
		});

		it('schedules timeout correctly for different durations', () => {
			toasts.trigger('100ms', 'info', 100);
			vi.advanceTimersByTime(1);
			toasts.trigger('200ms', 'info', 200);
			vi.advanceTimersByTime(1);
			toasts.trigger('300ms', 'info', 300);

			let currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(3);

			vi.advanceTimersByTime(100);
			currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(2);

			vi.advanceTimersByTime(100);
			currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);

			vi.advanceTimersByTime(100);
			currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(0);
		});
	});

	describe('remove', () => {
		it('removes a toast by ID', () => {
			toasts.trigger('Remove me', 'info', 0);
			const currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);

			const toastId = currentToasts[0].id;
			toasts.remove(toastId);

			const updatedToasts = get(toasts);
			expect(updatedToasts).toHaveLength(0);
		});

		it('removes the correct toast when multiple exist', () => {
			toasts.trigger('First', 'info', 0);
			vi.advanceTimersByTime(1);
			toasts.trigger('Second', 'info', 0);
			vi.advanceTimersByTime(1);
			toasts.trigger('Third', 'info', 0);

			let currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(3);

			const secondToastId = currentToasts[1].id;
			toasts.remove(secondToastId);

			currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(2);
			expect(currentToasts[0].message).toBe('First');
			expect(currentToasts[1].message).toBe('Third');
		});

		it('does nothing when removing non-existent ID', () => {
			toasts.trigger('Existing', 'info', 0);

			let currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);

			toasts.remove(99999);

			currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);
			expect(currentToasts[0].message).toBe('Existing');
		});

		it('can remove multiple toasts in sequence', () => {
			toasts.trigger('First', 'info', 0);
			vi.advanceTimersByTime(1);
			toasts.trigger('Second', 'info', 0);
			vi.advanceTimersByTime(1);
			toasts.trigger('Third', 'info', 0);

			let currentToasts = get(toasts);
			const ids = currentToasts.map((t) => t.id);

			toasts.remove(ids[0]);
			toasts.remove(ids[1]);
			toasts.remove(ids[2]);

			currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(0);
		});
	});

	describe('subscribe', () => {
		it('allows subscribing to toast updates', () => {
			const values: Toast[][] = [];
			const unsubscribe = toasts.subscribe((current) => {
				values.push([...current]);
			});

			toasts.trigger('Test');

			expect(values.length).toBeGreaterThan(0);
			const latestValue = values[values.length - 1];
			expect(latestValue).toHaveLength(1);
			expect(latestValue[0].message).toBe('Test');

			unsubscribe();
		});

		it('notifies subscribers when toast is added', () => {
			let notificationCount = 0;
			const unsubscribe = toasts.subscribe(() => {
				notificationCount++;
			});

			// Subscription triggers initial notification (count = 1)
			expect(notificationCount).toBe(1);

			toasts.trigger('First');
			expect(notificationCount).toBe(2);

			toasts.trigger('Second');
			expect(notificationCount).toBe(3);

			unsubscribe();
		});

		it('notifies subscribers when toast is removed', () => {
			toasts.trigger('Remove me', 'info', 0);
			const currentToasts = get(toasts);
			const toastId = currentToasts[0].id;

			let notificationCount = 0;
			const unsubscribe = toasts.subscribe(() => {
				notificationCount++;
			});

			// Subscription triggers initial notification (count = 1)
			expect(notificationCount).toBe(1);

			toasts.remove(toastId);
			expect(notificationCount).toBe(2);

			unsubscribe();
		});

		it('notifies subscribers when toast auto-expires', () => {
			let lastValue: Toast[] = [];
			const unsubscribe = toasts.subscribe((current) => {
				lastValue = [...current];
			});

			toasts.trigger('Expires', 'info', 1000);
			expect(lastValue).toHaveLength(1);

			vi.advanceTimersByTime(1000);
			expect(lastValue).toHaveLength(0);

			unsubscribe();
		});
	});

	describe('integration scenarios', () => {
		it('handles complex workflow: add, wait, add more, remove manually', () => {
			// Add first toast
			toasts.trigger('First', 'info', 2000);
			let currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);

			// Add second toast
			vi.advanceTimersByTime(1);
			toasts.trigger('Second', 'success', 3000);
			currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(2);

			// Manually remove first
			const firstId = currentToasts[0].id;
			toasts.remove(firstId);
			currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(1);
			expect(currentToasts[0].message).toBe('Second');

			// Wait for second to auto-expire
			vi.advanceTimersByTime(3000);
			currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(0);
		});

		it('handles all toast types in sequence', () => {
			const types: ToastType[] = ['success', 'error', 'info'];

			types.forEach((type) => {
				toasts.trigger(`${type} message`, type, 0);
				vi.advanceTimersByTime(1);
			});

			const currentToasts = get(toasts);
			expect(currentToasts).toHaveLength(3);
			expect(currentToasts[0].type).toBe('success');
			expect(currentToasts[1].type).toBe('error');
			expect(currentToasts[2].type).toBe('info');
		});

		it('maintains correct order when adding and removing toasts', () => {
			toasts.trigger('A', 'info', 0);
			vi.advanceTimersByTime(1);
			toasts.trigger('B', 'info', 0);
			vi.advanceTimersByTime(1);
			toasts.trigger('C', 'info', 0);

			let currentToasts = get(toasts);
			expect(currentToasts.map((t) => t.message)).toEqual(['A', 'B', 'C']);

			// Remove middle toast
			const middleId = currentToasts[1].id;
			toasts.remove(middleId);

			currentToasts = get(toasts);
			expect(currentToasts.map((t) => t.message)).toEqual(['A', 'C']);

			// Add another
			vi.advanceTimersByTime(1);
			toasts.trigger('D', 'info', 0);
			currentToasts = get(toasts);
			expect(currentToasts.map((t) => t.message)).toEqual(['A', 'C', 'D']);
		});
	});
});
