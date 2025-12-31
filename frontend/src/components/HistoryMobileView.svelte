<script lang="ts">
	import { Clock, Mail, CheckCircle, XCircle, AlertCircle, Search, Edit2 } from 'lucide-svelte';
	import { formatDate } from '../lib/dateUtils';
	import type { ComponentType } from 'svelte';

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

	interface HistoryMobileViewProps {
		emails: Email[];
		loading: boolean;
		onEmailClick: (email: Email) => void;
		onAnalyzeClick: (email: Email) => void;
		onCategoryEditClick: (email: Email) => void;
	}

	let {
		emails,
		loading,
		onEmailClick,
		onAnalyzeClick,
		onCategoryEditClick
	}: HistoryMobileViewProps = $props();

	function formatAmount(amount?: number) {
		if (amount === undefined || amount === null) return '-';
		return `$${amount.toFixed(2)}`;
	}

	function getStatusIcon(status: string): ComponentType {
		switch (status) {
			case 'forwarded':
				return CheckCircle;
			case 'blocked':
			case 'ignored':
				return XCircle;
			case 'error':
				return AlertCircle;
			default:
				return Mail;
		}
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'forwarded':
				return 'bg-emerald-100 text-emerald-800 border-emerald-200';
			case 'blocked':
			case 'ignored':
				return 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700';
			case 'error':
				return 'bg-red-100 text-red-800 border-red-200';
			default:
				return 'bg-blue-100 text-blue-600 border-blue-200';
		}
	}
</script>

<div class="md:hidden space-y-4 pb-20">
	{#if loading}
		<div class="card py-12 text-center text-text-secondary dark:text-text-secondary-dark">
			<Clock size={24} class="animate-spin mx-auto mb-2 text-primary" />
			<p>Loading your history...</p>
		</div>
	{:else if emails.length === 0}
		<div class="card py-12 text-center text-text-secondary dark:text-text-secondary-dark">
			<Mail size={32} class="mx-auto mb-2 text-gray-300" />
			<p>No activity found.</p>
		</div>
	{:else}
		{#each emails ?? [] as email (email.id)}
			{@const StatusIcon = getStatusIcon(email.status)}
			<div
				class="card border-l-4 {email.status === 'forwarded'
					? 'border-l-emerald-500'
					: email.status === 'error'
						? 'border-l-red-500'
						: 'border-l-gray-300'} p-4 active:scale-[0.98] transition-all"
			>
				<div class="flex justify-between items-start mb-2">
					{#if email.status === 'ignored'}
						<button
							onclick={() => onEmailClick(email)}
							class="badge {getStatusColor(email.status)} flex items-center gap-1 py-1 px-3 shadow-sm"
						>
							<StatusIcon size={12} />
							{email.status}
						</button>
					{:else if email.status === 'forwarded' || email.status === 'blocked'}
						<button
							onclick={() => onEmailClick(email)}
							class="badge {getStatusColor(email.status)} flex items-center gap-1 py-1 px-3 shadow-sm"
						>
							<StatusIcon size={12} />
							{email.status}
						</button>
					{:else}
						<div
							class="badge {getStatusColor(email.status)} flex items-center gap-1 py-1 px-3 shadow-sm"
						>
							<StatusIcon size={12} />
							{email.status}
						</div>
					{/if}
					<span
						class="text-[10px] font-medium text-gray-400 bg-gray-50 dark:bg-gray-800 dark:text-gray-500 px-2 py-1 rounded"
					>
						{formatDate(email.processed_at)}
					</span>
				</div>

				<h4 class="text-sm font-bold text-text-main line-clamp-2 mb-1 leading-snug">
					{email.subject}
				</h4>

				<div class="flex items-center gap-2 mb-3">
					<p class="text-xs text-text-secondary truncate flex-1">
						{email.sender}
					</p>
					{#if email.amount}
						<span class="text-xs font-bold text-primary bg-primary/5 px-2 py-0.5 rounded">
							{formatAmount(email.amount)}
						</span>
					{/if}
				</div>

				<div class="flex items-center justify-between pt-3 border-t border-gray-50">
					<button
						onclick={() => onCategoryEditClick(email)}
						class="text-[10px] text-gray-400 hover:text-primary transition-colors flex items-center gap-1"
						title="Edit category"
					>
						{email.category ? `#${email.category}` : '#unsorted'}
						<Edit2 size={12} />
					</button>
					<button
						onclick={() => onAnalyzeClick(email)}
						class="text-xs font-medium text-primary flex items-center gap-1 hover:underline"
					>
						<Search size={14} />
						View Details
					</button>
				</div>
			</div>
		{/each}
	{/if}
</div>
