<script lang="ts">
	import {
		CheckCircle,
		AlertCircle,
		RefreshCw,
		X,
		ThumbsUp,
		ThumbsDown
	} from 'lucide-svelte';

	interface Email {
		id: number;
		email_id: string;
		subject: string;
		sender: string;
		received_at: string;
		processed_at: string;
		status: string;
		account_email?: string;
		category?: string;
		amount?: number;
		reason?: string;
	}

	interface AnalysisOutcome {
		email_id: number;
		analysis: {
			steps: Array<{
				step: string;
				result: boolean;
				detail?: string;
			}>;
			final_decision: boolean;
		};
	}

	interface EmailDetailsModalProps {
		isOpen: boolean;
		selectedEmail: Email | null;
		isProcessing: boolean;
		isAnalyzing: boolean;
		selectedAnalysis: AnalysisOutcome | null;
		successMessage: string;
		errorMessage: string;
		onClose: () => void;
		onConfirmToggle: () => void;
		onConfirmToggleToIgnored: () => void;
		onSubmitFeedback: (isReceipt: boolean) => void;
	}

	let {
		isOpen,
		selectedEmail,
		isProcessing,
		isAnalyzing,
		selectedAnalysis,
		successMessage,
		errorMessage,
		onClose,
		onConfirmToggle,
		onConfirmToggleToIgnored,
		onSubmitFeedback
	}: EmailDetailsModalProps = $props();

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && isOpen) {
			onClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if isOpen && selectedEmail}
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<!-- Backdrop -->
		<div
			class="absolute inset-0 bg-black bg-opacity-50"
			onclick={onClose}
			onkeydown={(e) => e.key === 'Enter' && onClose()}
			role="button"
			tabindex="0"
			aria-label="Close modal backdrop"
		></div>

		<!-- Modal Content -->
		<div
			class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6 z-10"
			role="dialog"
			aria-modal="true"
			aria-labelledby="modal-title"
			aria-describedby="modal-description"
		>
			<!-- Modal Header -->
			<div class="flex items-center justify-between mb-4">
				<h3 id="modal-title" class="text-lg font-bold text-text-main dark:text-text-main-dark">
					{#if selectedEmail.status === 'ignored'}
						Forward Ignored Email
					{:else if selectedEmail.status === 'forwarded' || selectedEmail.status === 'blocked'}
						Change Email Status
					{:else}
						Email Details
					{/if}
				</h3>
				<button
					onclick={onClose}
					class="p-1 hover:bg-gray-100 rounded-lg transition-colors"
					title="Close"
					aria-label="Close modal"
				>
					<X size={20} class="text-text-secondary dark:text-text-secondary-dark" />
				</button>
			</div>

			<!-- Success Message -->
			{#if successMessage}
				<div
					class="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-start gap-2"
				>
					<CheckCircle size={20} class="text-emerald-600 shrink-0 mt-0.5" />
					<p class="text-sm text-emerald-800">{successMessage}</p>
				</div>
			{/if}

			<!-- Error Message -->
			{#if errorMessage}
				<div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
					<AlertCircle size={20} class="text-red-600 shrink-0 mt-0.5" />
					<p class="text-sm text-red-800">{errorMessage}</p>
				</div>
			{/if}

			<!-- Modal Content -->
			<div class="mb-6">
				{#if isAnalyzing}
					<div class="py-12 text-center">
						<RefreshCw size={24} class="animate-spin text-primary mx-auto mb-2" />
						<p class="text-sm text-text-secondary dark:text-text-secondary-dark">
							Analyzing rule logic...
						</p>
					</div>
				{:else if selectedAnalysis}
					<div class="mb-4">
						<h4 class="text-sm font-bold text-text-main mb-2">Detection Trace</h4>
						<div
							class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2 max-h-40 overflow-y-auto"
						>
							{#each selectedAnalysis.analysis.steps as step (step.step)}
								<div class="flex items-center justify-between text-xs">
									<span class="text-text-secondary dark:text-text-secondary-dark">{step.step}:</span>
									<span class={step.result ? 'text-emerald-600 font-bold' : 'text-red-500'}>
										{step.result ? 'MATCH' : 'MISS'}
									</span>
								</div>
								{#if step.detail}
									<p class="text-[10px] text-gray-400 italic ml-2">{step.detail}</p>
								{/if}
							{/each}
						</div>
						<div
							class="mt-3 p-2 rounded {selectedAnalysis.analysis.final_decision
								? 'bg-emerald-50 text-emerald-700'
								: 'bg-red-50 text-red-700'} text-xs font-bold text-center"
						>
							Final Decision: {selectedAnalysis.analysis.final_decision
								? 'RECEIPT'
								: 'NOT A RECEIPT'}
						</div>
					</div>
				{/if}

				<p id="modal-description" class="text-text-secondary mb-4 text-sm">
					Help improve the adaptive rule engine by providing feedback.
				</p>

				<div
					class="bg-gray-50 rounded-lg p-4 space-y-2 border border-gray-100 dark:border-gray-700"
				>
					<div>
						<span class="text-xs font-semibold text-text-secondary uppercase">Subject:</span>
						<p class="text-sm text-text-main font-medium break-all">{selectedEmail.subject}</p>
					</div>
					<div>
						<span class="text-xs font-semibold text-text-secondary uppercase">Sender:</span>
						<p class="text-sm text-text-main break-all">{selectedEmail.sender}</p>
					</div>
				</div>
			</div>

			<!-- Modal Actions -->
			<div class="flex flex-wrap gap-3 justify-between">
				<div class="flex gap-2">
					<button
						onclick={() => onSubmitFeedback(true)}
						class="btn btn-secondary border-emerald-200 text-emerald-700 hover:bg-emerald-50"
						disabled={isProcessing}
						title="Mark as SHOULD have been a receipt"
					>
						<ThumbsUp size={16} />
					</button>
					<button
						onclick={() => onSubmitFeedback(false)}
						class="btn btn-secondary border-red-200 text-red-700 hover:bg-red-50"
						disabled={isProcessing}
						title="Mark as NOT a receipt"
					>
						<ThumbsDown size={16} />
					</button>
				</div>

				<div class="flex gap-2">
					<button onclick={onClose} class="btn btn-secondary" disabled={isProcessing}>
						Close
					</button>
					{#if selectedEmail.status === 'ignored'}
						<button onclick={onConfirmToggle} class="btn btn-primary" disabled={isProcessing}>
							{#if isProcessing}
								<RefreshCw size={16} class="animate-spin" />
							{:else}
								<RefreshCw size={16} />
								Forward & Create Rule
							{/if}
						</button>
					{:else if selectedEmail.status === 'forwarded' || selectedEmail.status === 'blocked'}
						<button
							onclick={onConfirmToggleToIgnored}
							class="btn btn-primary"
							disabled={isProcessing}
						>
							{#if isProcessing}
								<RefreshCw size={16} class="animate-spin" />
							{:else}
								<RefreshCw size={16} />
								Change to Ignored
							{/if}
						</button>
					{/if}
				</div>
			</div>
		</div>
	</div>
{/if}
