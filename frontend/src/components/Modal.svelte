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

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && isOpen) {
			onClose();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if isOpen}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
		on:click={handleBackdropClick}
	>
		<div
			class="relative w-full max-w-md mx-4 bg-bg-card rounded-xl shadow-2xl border border-border transform transition-all"
			role="dialog"
			aria-modal="true"
			aria-labelledby={title ? 'modal-title' : undefined}
		>
			{#if title || showCloseButton}
				<div class="flex items-center justify-between p-6 pb-4 border-b border-border">
					{#if title}
						<h3 id="modal-title" class="text-xl font-bold text-text-main">{title}</h3>
					{:else}
						<div></div>
					{/if}
					{#if showCloseButton}
						<button
							on:click={onClose}
							class="p-1 rounded-lg text-text-secondary hover:text-text-main hover:bg-gray-100 transition-colors"
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
