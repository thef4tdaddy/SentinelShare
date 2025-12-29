import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Modal from './Modal.svelte';

describe('Modal Component', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	// Helper function to get modal content area
	const getModalContent = (container: HTMLElement) => {
		return container.querySelector('div[role="dialog"] > div:last-child');
	};

	// Helper function to render modal with two focusable buttons
	const renderModalWithTwoButtons = () => {
		const onClose = vi.fn();
		const { container } = render(Modal, {
			isOpen: true,
			onClose,
			title: 'Test Modal',
			showCloseButton: true
		});

		// Wait for modal to be rendered
		return new Promise<{ container: HTMLElement; onClose: ReturnType<typeof vi.fn> }>((resolve) => {
			setTimeout(() => {
				// Add a second button to the modal content
				const modalContent = getModalContent(container);
				const secondButton = document.createElement('button');
				secondButton.textContent = 'Second Button';
				secondButton.setAttribute('data-testid', 'second-button');
				modalContent?.appendChild(secondButton);
				resolve({ container, onClose });
			}, 10);
		});
	};

	// Helper function to render modal with non-focusable content
	const renderModalWithNonFocusableContent = () => {
		const onClose = vi.fn();
		const { container } = render(Modal, {
			isOpen: true,
			onClose,
			showCloseButton: false
		});

		// Wait for modal to be rendered
		return new Promise<{ container: HTMLElement; onClose: ReturnType<typeof vi.fn> }>((resolve) => {
			setTimeout(() => {
				// Add non-focusable content to the modal
				const modalContent = getModalContent(container);
				const div = document.createElement('div');
				div.textContent = 'Just text content';
				modalContent?.appendChild(div);
				resolve({ container, onClose });
			}, 10);
		});
	};

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
		render(Modal, {
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

	it('traps focus when Tab is pressed at the last element', async () => {
		await renderModalWithTwoButtons();

		// Focus the close button (first element)
		const closeButton = screen.getByLabelText('Close');
		closeButton.focus();
		expect(document.activeElement).toBe(closeButton);

		// Focus the second button (last element)
		const secondButton = screen.getByTestId('second-button');
		secondButton.focus();
		expect(document.activeElement).toBe(secondButton);

		// Press Tab when on last element - should cycle to first
		await fireEvent.keyDown(window, { key: 'Tab' });

		// Small delay for focus to change
		await new Promise((resolve) => setTimeout(resolve, 10));

		expect(document.activeElement).toBe(closeButton);
	});

	it('traps focus when Shift+Tab is pressed at the first element', async () => {
		await renderModalWithTwoButtons();

		// Get both buttons
		const closeButton = screen.getByLabelText('Close');
		const secondButton = screen.getByTestId('second-button');

		// Focus the first element (close button)
		closeButton.focus();
		expect(document.activeElement).toBe(closeButton);

		// Press Shift+Tab when on first element - should cycle to last
		await fireEvent.keyDown(window, { key: 'Tab', shiftKey: true });

		// Small delay for focus to change
		await new Promise((resolve) => setTimeout(resolve, 10));

		expect(document.activeElement).toBe(secondButton);
	});

	it('does nothing when Tab is pressed and there are no focusable elements', async () => {
		await renderModalWithNonFocusableContent();

		const activeElementBefore = document.activeElement;

		// Press Tab
		await fireEvent.keyDown(window, { key: 'Tab' });

		// Should not change focus or throw error
		expect(document.activeElement).toBe(activeElementBefore);
	});

	it('focuses the modal element when there are no focusable children', async () => {
		await renderModalWithNonFocusableContent();

		// The modal element itself should be focused
		const dialog = screen.getByRole('dialog');
		expect(document.activeElement).toBe(dialog);
	});

	it('restores focus to previously focused element when modal closes', async () => {
		const onClose = vi.fn();

		// Create a button outside the modal to focus initially
		const externalButton = document.createElement('button');
		externalButton.textContent = 'External Button';
		externalButton.setAttribute('data-testid', 'external-button');
		document.body.appendChild(externalButton);
		externalButton.focus();

		expect(document.activeElement).toBe(externalButton);

		// Render modal with isOpen=true
		const { rerender } = render(Modal, {
			isOpen: true,
			onClose,
			title: 'Test Modal',
			showCloseButton: true
		});

		// Wait for modal focus
		await new Promise((resolve) => setTimeout(resolve, 10));

		// Focus should have moved to modal
		const closeButton = screen.getByLabelText('Close');
		expect(document.activeElement).toBe(closeButton);

		// Close the modal by changing isOpen to false
		rerender({
			isOpen: false,
			onClose,
			title: 'Test Modal',
			showCloseButton: true
		});

		// Wait for focus restoration
		await new Promise((resolve) => setTimeout(resolve, 10));

		// Focus should be restored to the external button
		expect(document.activeElement).toBe(externalButton);

		// Cleanup
		document.body.removeChild(externalButton);
	});
});
