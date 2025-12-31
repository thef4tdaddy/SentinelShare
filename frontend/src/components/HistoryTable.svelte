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

	interface HistoryTableProps {
		emails: Email[];
		loading: boolean;
		onEmailClick: (email: Email) => void;
		onAnalyzeClick: (email: Email) => void;
		onCategoryEditClick: (email: Email) => void;
	}

	let { emails, loading, onEmailClick, onAnalyzeClick, onCategoryEditClick }: HistoryTableProps =
		$props();

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

<div class="hidden md:block card overflow-hidden">
	<div class="overflow-x-auto">
		<table class="w-full text-left border-collapse">
			<thead>
				<tr class="border-b border-gray-100 dark:border-gray-700">
					<th
						class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50 dark:bg-gray-800/50"
					>
						Status
					</th>
					<th
						class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50 dark:bg-gray-800/50"
					>
						Subject
					</th>
					<th
						class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50 dark:bg-gray-800/50"
					>
						Sender
					</th>
					<th
						class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50 dark:bg-gray-800/50"
					>
						Category
					</th>
					<th
						class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50 dark:bg-gray-800/50"
					>
						Amount
					</th>
					<th
						class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50 dark:bg-gray-800/50"
					>
						Processed
					</th>
				</tr>
			</thead>
			<tbody>
				{#if loading}
					<tr>
						<td
							colspan="6"
							class="py-12 text-center text-text-secondary dark:text-text-secondary-dark"
						>
							<div class="flex items-center justify-center gap-2">
								<Clock size={20} class="animate-spin" />
								Loading...
							</div>
						</td>
					</tr>
				{:else if emails?.length === 0}
					<tr>
						<td
							colspan="6"
							class="py-12 text-center text-text-secondary dark:text-text-secondary-dark"
						>
							<div class="flex flex-col items-center justify-center gap-3">
								<div class="bg-gray-100 dark:bg-gray-800 p-3 rounded-full">
									<Mail size={24} class="text-gray-400 dark:text-gray-500" />
								</div>
								<p>No emails found.</p>
							</div>
						</td>
					</tr>
				{:else}
					{#each emails ?? [] as email (email.id)}
						{@const StatusIcon = getStatusIcon(email.status)}
						<tr
							class="border-b border-gray-50 last:border-0 hover:bg-gray-50/80 transition-colors"
						>
							<td class="py-3 px-4">
								{#if email.status === 'ignored'}
									<button
										onclick={() => onEmailClick(email)}
										class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize shadow-sm {getStatusColor(
											email.status
										)} cursor-pointer hover:opacity-80 transition-opacity"
										title="Click to forward and create rule"
									>
										<StatusIcon size={12} class="mr-1" />
										{email.status}
									</button>
								{:else if email.status === 'forwarded' || email.status === 'blocked'}
									<button
										onclick={() => onEmailClick(email)}
										class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize shadow-sm {getStatusColor(
											email.status
										)} cursor-pointer hover:opacity-80 transition-opacity"
										title="Click to change to ignored"
									>
										<StatusIcon size={12} class="mr-1" />
										{email.status}
									</button>
								{:else}
									<span
										class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize shadow-sm {getStatusColor(
											email.status
										)}"
									>
										<StatusIcon size={12} class="mr-1" />
										{email.status}
									</span>
								{/if}
								<button
									onclick={() => onAnalyzeClick(email)}
									class="ml-2 p-1 text-gray-400 hover:text-primary transition-colors"
									title="Analyze Detection Logic"
								>
									<Search size={14} />
								</button>
							</td>
							<td class="py-3 px-4 font-medium text-text-main dark:text-text-main-dark">
								<div class="truncate max-w-[300px]" title={email.subject}>
									{email.subject}
								</div>
								{#if email.reason}
									<div class="text-xs text-text-secondary mt-1">{email.reason}</div>
								{/if}
							</td>
							<td class="py-3 px-4 text-text-secondary text-sm">
								<div class="truncate max-w-[200px]" title={email.sender}>
									{email.sender}
								</div>
								{#if email.account_email}
									<div class="text-xs text-gray-400 mt-1">via {email.account_email}</div>
								{/if}
							</td>
							<td class="py-3 px-4 text-text-secondary text-sm">
								<div class="flex items-center gap-2">
									<span>{email.category || '-'}</span>
									<button
										onclick={() => onCategoryEditClick(email)}
										class="p-1 text-gray-400 hover:text-primary transition-colors"
										title="Edit Category"
										aria-label="Edit category"
									>
										<Edit2 size={14} />
									</button>
								</div>
							</td>
							<td class="py-3 px-4 text-text-secondary text-sm">
								{formatAmount(email.amount)}
							</td>
							<td class="py-3 px-4 text-text-secondary text-sm whitespace-nowrap">
								{formatDate(email.processed_at)}
							</td>
						</tr>
					{/each}
				{/if}
			</tbody>
		</table>
	</div>
</div>
