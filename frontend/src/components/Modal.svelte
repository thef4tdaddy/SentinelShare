<script lang="ts">
	import { X } from 'lucide-svelte';
	import type { Snippet } from 'svelte';

	interface ModalProps {
		isOpen: boolean;
		onClose: () => void;
		title?: string;
		showCloseButton?: boolean;
		children?: Snippet;
	}

	let {
		isOpen = $bindable(),
		onClose,
		title,
		showCloseButton = true,
		children
	}: ModalProps = $props();

	let modalElement: HTMLDivElement | undefined = $state();
	let previouslyFocusedElement: HTMLElement | null = null;

	// Selector for focusable elements
	const FOCUSABLE_SELECTOR =
		'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && isOpen) {
			onClose();
		}

		// Handle Tab key for focus trapping
		if (e.key === 'Tab' && isOpen && modalElement) {
			const focusableElements = modalElement.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
			const focusableArray = Array.from(focusableElements);

			if (focusableArray.length === 0) return;

			const firstElement = focusableArray[0];
			const lastElement = focusableArray[focusableArray.length - 1];

			if (e.shiftKey) {
				// Shift + Tab
				if (document.activeElement === firstElement) {
					e.preventDefault();
					lastElement.focus();
				}
			} else {
				// Tab
				if (document.activeElement === lastElement) {
					e.preventDefault();
					firstElement.focus();
				}
			}
		}
	}

	$effect(() => {
		if (isOpen) {
			// Store the currently focused element
			previouslyFocusedElement = document.activeElement as HTMLElement;

			// Focus the modal after a brief delay to ensure it's rendered
			setTimeout(() => {
				if (modalElement) {
					const focusableElements = modalElement.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
					if (focusableElements.length > 0) {
						focusableElements[0].focus();
					} else {
						modalElement.focus();
					}
				}
			}, 0);
		} else {
			// Restore focus when modal closes
			if (previouslyFocusedElement) {
				previouslyFocusedElement.focus();
				previouslyFocusedElement = null;
			}
		}
	});
</script>

<svelte:window onkeydown={handleKeydown} />

{#if isOpen}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
		onclick={handleBackdropClick}
		onkeydown={handleKeydown}
		role="button"
		tabindex="-1"
		aria-label="Close modal"
	>
		<div
			bind:this={modalElement}
			class="relative w-full max-w-md mx-4 bg-bg-card rounded-xl shadow-2xl border border-border transform transition-all dark:bg-bg-card-dark dark:border-border-dark"
			role="dialog"
			aria-modal="true"
			aria-labelledby={title ? 'modal-title' : undefined}
			tabindex="-1"
		>
			{#if title || showCloseButton}
				<div class="flex items-center justify-between p-6 pb-4 border-b border-border dark:border-border-dark">
					{#if title}
						<h3 id="modal-title" class="text-xl font-bold text-text-main dark:text-text-main-dark">{title}</h3>
					{:else}
						<div></div>
					{/if}
					{#if showCloseButton}
						<button
							onclick={onClose}
							class="p-1 rounded-lg text-text-secondary hover:text-text-main hover:bg-gray-100 transition-colors dark:text-text-secondary-dark dark:hover:text-text-main-dark dark:hover:bg-gray-800"
							aria-label="Close"
						>
							<X size={20} />
						</button>
					{/if}
				</div>
			{/if}

			<div class="p-6">
				{@render children?.()}
			</div>
		</div>
	</div>
{/if}
