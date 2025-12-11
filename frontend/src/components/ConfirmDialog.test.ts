import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ConfirmDialog from './ConfirmDialog.svelte';

describe('ConfirmDialog Component', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('renders with default title and message', () => {
		const onConfirm = vi.fn();
		const onCancel = vi.fn();

		render(ConfirmDialog, {
			isOpen: true,
			onConfirm,
			onCancel,
			message: 'Are you sure you want to proceed?'
		});

		expect(screen.getByText('Confirm Action')).toBeTruthy();
		expect(screen.getByText('Are you sure you want to proceed?')).toBeTruthy();
	});

	it('renders with custom title', () => {
		const onConfirm = vi.fn();
		const onCancel = vi.fn();

		render(ConfirmDialog, {
			isOpen: true,
			onConfirm,
			onCancel,
			title: 'Delete Item',
			message: 'This action cannot be undone.'
		});

		expect(screen.getByText('Delete Item')).toBeTruthy();
		expect(screen.getByText('This action cannot be undone.')).toBeTruthy();
	});

	it('renders with custom button text', () => {
		const onConfirm = vi.fn();
		const onCancel = vi.fn();

		render(ConfirmDialog, {
			isOpen: true,
			onConfirm,
			onCancel,
			message: 'Proceed?',
			confirmText: 'Yes',
			cancelText: 'No'
		});

		expect(screen.getByText('Yes')).toBeTruthy();
		expect(screen.getByText('No')).toBeTruthy();
	});

	it('calls onConfirm when confirm button is clicked', async () => {
		const onConfirm = vi.fn();
		const onCancel = vi.fn();

		render(ConfirmDialog, {
			isOpen: true,
			onConfirm,
			onCancel,
			message: 'Proceed?',
			confirmText: 'Confirm',
			cancelText: 'Cancel'
		});

		const confirmButton = screen.getByText('Confirm');
		await fireEvent.click(confirmButton);

		expect(onConfirm).toHaveBeenCalledTimes(1);
		expect(onCancel).not.toHaveBeenCalled();
	});

	it('calls onCancel when cancel button is clicked', async () => {
		const onConfirm = vi.fn();
		const onCancel = vi.fn();

		render(ConfirmDialog, {
			isOpen: true,
			onConfirm,
			onCancel,
			message: 'Proceed?',
			confirmText: 'Confirm',
			cancelText: 'Cancel'
		});

		const cancelButton = screen.getByText('Cancel');
		await fireEvent.click(cancelButton);

		expect(onCancel).toHaveBeenCalledTimes(1);
		expect(onConfirm).not.toHaveBeenCalled();
	});

	it('renders danger icon when danger is true', () => {
		const onConfirm = vi.fn();
		const onCancel = vi.fn();

		const { container } = render(ConfirmDialog, {
			isOpen: true,
			onConfirm,
			onCancel,
			message: 'Delete this item?',
			danger: true
		});

		// Check for the AlertCircle icon (danger icon)
		const dangerIcon = container.querySelector('.text-danger');
		expect(dangerIcon).toBeTruthy();
	});

	it('does not render danger icon when danger is false', () => {
		const onConfirm = vi.fn();
		const onCancel = vi.fn();

		const { container } = render(ConfirmDialog, {
			isOpen: true,
			onConfirm,
			onCancel,
			message: 'Proceed?',
			danger: false
		});

		// Check that the AlertCircle icon is not present
		const dangerIcon = container.querySelector('.text-danger');
		expect(dangerIcon).toBeNull();
	});

	it('applies danger styling to confirm button when danger is true', () => {
		const onConfirm = vi.fn();
		const onCancel = vi.fn();

		const { container } = render(ConfirmDialog, {
			isOpen: true,
			onConfirm,
			onCancel,
			message: 'Delete this item?',
			confirmText: 'Delete',
			danger: true
		});

		const confirmButton = screen.getByText('Delete');
		expect(confirmButton.classList.contains('btn-danger')).toBe(true);
	});

	it('applies primary styling to confirm button when danger is false', () => {
		const onConfirm = vi.fn();
		const onCancel = vi.fn();

		const { container } = render(ConfirmDialog, {
			isOpen: true,
			onConfirm,
			onCancel,
			message: 'Proceed?',
			confirmText: 'Confirm',
			danger: false
		});

		const confirmButton = screen.getByText('Confirm');
		expect(confirmButton.classList.contains('btn-primary')).toBe(true);
	});

	it('does not render when isOpen is false', () => {
		const onConfirm = vi.fn();
		const onCancel = vi.fn();

		render(ConfirmDialog, {
			isOpen: false,
			onConfirm,
			onCancel,
			message: 'Proceed?'
		});

		expect(screen.queryByText('Proceed?')).toBeNull();
	});

	it('calls onCancel when Escape key is pressed', async () => {
		const onConfirm = vi.fn();
		const onCancel = vi.fn();

		render(ConfirmDialog, {
			isOpen: true,
			onConfirm,
			onCancel,
			message: 'Proceed?'
		});

		await fireEvent.keyDown(window, { key: 'Escape' });

		expect(onCancel).toHaveBeenCalledTimes(1);
		expect(onConfirm).not.toHaveBeenCalled();
	});
});
