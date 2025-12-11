<script lang="ts">
	import Modal from './Modal.svelte';
	import { AlertCircle } from 'lucide-svelte';

	interface ConfirmDialogProps {
		isOpen: boolean;
		onConfirm: () => void;
		onCancel: () => void;
		title?: string;
		message: string;
		confirmText?: string;
		cancelText?: string;
		danger?: boolean;
	}

	let {
		isOpen = $bindable(),
		onConfirm,
		onCancel,
		title = 'Confirm Action',
		message,
		confirmText = 'Confirm',
		cancelText = 'Cancel',
		danger = false
	}: ConfirmDialogProps = $props();
</script>

<Modal {isOpen} onClose={onCancel} {title} showCloseButton={false}>
	<div class="space-y-4">
		<div class="flex items-start gap-3">
			{#if danger}
				<div class="flex-shrink-0 mt-0.5">
					<AlertCircle class="text-danger" size={24} />
				</div>
			{/if}
			<p class="text-text-main text-base leading-relaxed">{message}</p>
		</div>

		<div class="flex gap-3 justify-end pt-2">
			<button on:click={onCancel} class="btn btn-secondary">
				{cancelText}
			</button>
			<button on:click={onConfirm} class="btn {danger ? 'btn-danger' : 'btn-primary'}">
				{confirmText}
			</button>
		</div>
	</div>
</Modal>
