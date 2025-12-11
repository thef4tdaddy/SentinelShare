import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Modal from './Modal.svelte';

describe('Modal Component', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('renders modal when isOpen is true', () => {
		const onClose = vi.fn();
		render(Modal, {
			isOpen: true,
			onClose,
			title: 'Test Modal'
		});

		expect(screen.getByText('Test Modal')).toBeTruthy();
		expect(screen.getByRole('dialog')).toBeTruthy();
	});

	it('does not render modal when isOpen is false', () => {
		const onClose = vi.fn();
		render(Modal, {
			isOpen: false,
			onClose,
			title: 'Test Modal'
		});

		expect(screen.queryByText('Test Modal')).toBeNull();
		expect(screen.queryByRole('dialog')).toBeNull();
	});

	it('renders modal without title', () => {
		const onClose = vi.fn();
		render(Modal, {
			isOpen: true,
			onClose
		});

		expect(screen.getByRole('dialog')).toBeTruthy();
		expect(screen.queryByRole('heading')).toBeNull();
	});

	it('renders close button when showCloseButton is true', () => {
		const onClose = vi.fn();
		render(Modal, {
			isOpen: true,
			onClose,
			title: 'Test Modal',
			showCloseButton: true
		});

		const closeButton = screen.getByLabelText('Close');
		expect(closeButton).toBeTruthy();
	});

	it('does not render close button when showCloseButton is false', () => {
		const onClose = vi.fn();
		render(Modal, {
			isOpen: true,
			onClose,
			title: 'Test Modal',
			showCloseButton: false
		});

		expect(screen.queryByLabelText('Close')).toBeNull();
	});

	it('calls onClose when close button is clicked', async () => {
		const onClose = vi.fn();
		render(Modal, {
			isOpen: true,
			onClose,
			title: 'Test Modal',
			showCloseButton: true
		});

		const closeButton = screen.getByLabelText('Close');
		await fireEvent.click(closeButton);

		expect(onClose).toHaveBeenCalledTimes(1);
	});

	it('calls onClose when Escape key is pressed', async () => {
		const onClose = vi.fn();
		render(Modal, {
			isOpen: true,
			onClose,
			title: 'Test Modal'
		});

		await fireEvent.keyDown(window, { key: 'Escape' });

		expect(onClose).toHaveBeenCalledTimes(1);
	});

	it('does not call onClose when other keys are pressed', async () => {
		const onClose = vi.fn();
		render(Modal, {
			isOpen: true,
			onClose,
			title: 'Test Modal'
		});

		await fireEvent.keyDown(window, { key: 'Enter' });
		await fireEvent.keyDown(window, { key: 'Space' });

		expect(onClose).not.toHaveBeenCalled();
	});

	it('calls onClose when backdrop is clicked', async () => {
		const onClose = vi.fn();
		const { container } = render(Modal, {
			isOpen: true,
			onClose,
			title: 'Test Modal'
		});

		// Click on the backdrop (the outer div with backdrop-blur-sm)
		const backdrop = container.querySelector('.backdrop-blur-sm');
		if (backdrop) {
			await fireEvent.click(backdrop);
			expect(onClose).toHaveBeenCalledTimes(1);
		}
	});

	it('does not call onClose when modal content is clicked', async () => {
		const onClose = vi.fn();
		render(Modal, {
			isOpen: true,
			onClose,
			title: 'Test Modal'
		});

		const dialog = screen.getByRole('dialog');
		await fireEvent.click(dialog);

		expect(onClose).not.toHaveBeenCalled();
	});

	it('has correct accessibility attributes', () => {
		const onClose = vi.fn();
		render(Modal, {
			isOpen: true,
			onClose,
			title: 'Test Modal'
		});

		const dialog = screen.getByRole('dialog');
		expect(dialog.getAttribute('aria-modal')).toBe('true');
		expect(dialog.getAttribute('aria-labelledby')).toBe('modal-title');
	});

	it('has aria-labelledby undefined when no title is provided', () => {
		const onClose = vi.fn();
		render(Modal, {
			isOpen: true,
			onClose
		});

		const dialog = screen.getByRole('dialog');
		expect(dialog.getAttribute('aria-modal')).toBe('true');
		expect(dialog.getAttribute('aria-labelledby')).toBeNull();
	});

	it('focuses first focusable element when modal opens', async () => {
		const onClose = vi.fn();
		const { container } = render(Modal, {
			isOpen: true,
			onClose,
			title: 'Test Modal',
			showCloseButton: true
		});

		// Wait for focus to be set
		await new Promise((resolve) => setTimeout(resolve, 10));

		const closeButton = screen.getByLabelText('Close');
		expect(document.activeElement).toBe(closeButton);
	});
});
