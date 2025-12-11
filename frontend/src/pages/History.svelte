<script lang="ts">
	import { fetchJson } from '../lib/api';
	import { onMount } from 'svelte';
	import {
		Clock,
		Mail,
		CheckCircle,
		XCircle,
		AlertCircle,
		ChevronLeft,
		ChevronRight,
		History as HistoryIcon,
		RefreshCw,
		X
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

	interface Run {
		run_time: string;
		first_processed: string;
		last_processed: string;
		total_emails: number;
		forwarded: number;
		blocked: number;
		errors: number;
		email_ids: number[];
	}

	let emails: Email[] = [];
	let runs: Run[] = [];
	let stats = {
		total: 0,
		forwarded: 0,
		blocked: 0,
		errors: 0,
		total_amount: 0,
		status_breakdown: {}
	};

	let pagination = {
		page: 1,
		per_page: 50,
		total: 0,
		total_pages: 0
	};

	let filters = {
		status: '',
		date_from: '',
		date_to: ''
	};

	let loading = true;
	let activeTab: 'emails' | 'runs' = 'emails';
	let showModal = false;
	let selectedEmail: Email | null = null;
	let isProcessing = false;
	let successMessage = '';
	let errorMessage = '';

	async function loadHistory() {
		loading = true;
		try {
			// eslint-disable-next-line svelte/prefer-svelte-reactivity
			const params = new URLSearchParams({
				page: pagination.page.toString(),
				per_page: pagination.per_page.toString()
			});

			if (filters.status) params.append('status', filters.status);
			if (filters.date_from) params.append('date_from', filters.date_from);
			if (filters.date_to) params.append('date_to', filters.date_to);

			const [historyRes, statsRes, runsRes] = await Promise.all([
				fetchJson(`/history/emails?${params}`),
				fetchJson('/history/stats'),
				fetchJson('/history/runs')
			]);

			emails = historyRes.emails;
			pagination = historyRes.pagination;
			stats = statsRes;
			runs = runsRes.runs;
		} catch (e) {
			console.error('Failed to load history', e);
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadHistory();
		// Add keyboard event listener for Escape key
		window.addEventListener('keydown', handleKeydown);
		
		return () => {
			window.removeEventListener('keydown', handleKeydown);
		};
	});

	function handleFilterChange() {
		pagination.page = 1;
		loadHistory();
	}

	function goToPage(page: number) {
		pagination.page = page;
		loadHistory();
	}

	function formatDate(dateStr: string) {
		if (!dateStr) return '';
		return new Date(dateStr).toLocaleString(undefined, {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function formatAmount(amount?: number) {
		if (amount === undefined || amount === null) return '-';
		return `$${amount.toFixed(2)}`;
	}

	function getStatusIcon(status: string) {
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
				return 'bg-gray-100 text-gray-600 border-gray-200';
			case 'error':
				return 'bg-red-100 text-red-800 border-red-200';
			default:
				return 'bg-blue-100 text-blue-600 border-blue-200';
		}
	}

	function openModal(email: Email) {
		selectedEmail = email;
		showModal = true;
		successMessage = '';
		errorMessage = '';
		// Focus management will be handled by Svelte's auto-focus
	}

	function closeModal() {
		showModal = false;
		selectedEmail = null;
		successMessage = '';
		errorMessage = '';
		isProcessing = false;
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && showModal) {
			closeModal();
		}
	}

	async function confirmToggle() {
		if (!selectedEmail || isProcessing) return;

		isProcessing = true;
		errorMessage = '';
		successMessage = '';

		try {
			const result = await fetchJson('/actions/toggle-ignored', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email_id: selectedEmail.id })
			});

			successMessage = result.message || 'Email forwarded and rule created successfully!';
			
			// Wait a moment to show success message, then close and reload
			setTimeout(async () => {
				closeModal();
				await loadHistory();
			}, 1500);
		} catch (e: any) {
			console.error('Failed to toggle ignored email', e);
			// Extract error message from the response if available
			errorMessage = e?.message || e?.detail || 'Failed to forward email and create rule. Please try again.';
			isProcessing = false;
		}
	}
</script>

<div class="mb-8">
	<h2 class="text-2xl font-bold text-text-main mb-1">History</h2>
	<p class="text-text-secondary text-sm">
		Complete history of email processing and automated runs.
	</p>
</div>

<!-- Stats Cards -->
<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
	<div class="card">
		<div class="flex items-center justify-between">
			<div>
				<p class="text-text-secondary text-sm mb-1">Total Processed</p>
				<p class="text-2xl font-bold text-text-main">{stats.total}</p>
			</div>
			<div class="p-3 bg-blue-50 text-blue-600 rounded-lg">
				<Mail size={24} />
			</div>
		</div>
	</div>

	<div class="card">
		<div class="flex items-center justify-between">
			<div>
				<p class="text-text-secondary text-sm mb-1">Forwarded</p>
				<p class="text-2xl font-bold text-emerald-600">{stats.forwarded}</p>
			</div>
			<div class="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
				<CheckCircle size={24} />
			</div>
		</div>
	</div>

	<div class="card">
		<div class="flex items-center justify-between">
			<div>
				<p class="text-text-secondary text-sm mb-1">Blocked</p>
				<p class="text-2xl font-bold text-gray-600">{stats.blocked}</p>
			</div>
			<div class="p-3 bg-gray-50 text-gray-600 rounded-lg">
				<XCircle size={24} />
			</div>
		</div>
	</div>

	<div class="card">
		<div class="flex items-center justify-between">
			<div>
				<p class="text-text-secondary text-sm mb-1">Errors</p>
				<p class="text-2xl font-bold text-red-600">{stats.errors}</p>
			</div>
			<div class="p-3 bg-red-50 text-red-600 rounded-lg">
				<AlertCircle size={24} />
			</div>
		</div>
	</div>
</div>

<!-- Tabs -->
<div class="flex gap-2 mb-6 border-b border-gray-200">
	<button
		class="px-4 py-2 font-medium transition-all {activeTab === 'emails'
			? 'text-primary border-b-2 border-primary'
			: 'text-text-secondary hover:text-text-main'}"
		on:click={() => (activeTab = 'emails')}
	>
		All Emails
	</button>
	<button
		class="px-4 py-2 font-medium transition-all {activeTab === 'runs'
			? 'text-primary border-b-2 border-primary'
			: 'text-text-secondary hover:text-text-main'}"
		on:click={() => (activeTab = 'runs')}
	>
		Processing Runs
	</button>
</div>

{#if activeTab === 'emails'}
	<!-- Filters -->
	<div class="card mb-6">
		<div class="flex flex-wrap gap-4 items-end">
			<div class="flex-1 min-w-[200px]">
				<label for="status-filter" class="block text-sm font-medium text-text-main mb-2">
					Status
				</label>
				<select
					id="status-filter"
					bind:value={filters.status}
					on:change={handleFilterChange}
					class="input"
				>
					<option value="">All</option>
					<option value="forwarded">Forwarded</option>
					<option value="blocked">Blocked</option>
					<option value="ignored">Ignored</option>
					<option value="error">Error</option>
				</select>
			</div>

			<div class="flex-1 min-w-[200px]">
				<label for="date-from" class="block text-sm font-medium text-text-main mb-2">
					From Date
				</label>
				<input
					id="date-from"
					type="datetime-local"
					bind:value={filters.date_from}
					on:change={handleFilterChange}
					class="input"
				/>
			</div>

			<div class="flex-1 min-w-[200px]">
				<label for="date-to" class="block text-sm font-medium text-text-main mb-2"> To Date </label>
				<input
					id="date-to"
					type="datetime-local"
					bind:value={filters.date_to}
					on:change={handleFilterChange}
					class="input"
				/>
			</div>

			<button
				on:click={() => {
					filters = { status: '', date_from: '', date_to: '' };
					handleFilterChange();
				}}
				class="btn btn-secondary"
			>
				Clear Filters
			</button>
		</div>
	</div>

	<!-- Email History Table -->
	<div class="card overflow-hidden">
		<div class="overflow-x-auto">
			<table class="w-full text-left border-collapse">
				<thead>
					<tr class="border-b border-gray-100">
						<th
							class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50"
						>
							Status
						</th>
						<th
							class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50"
						>
							Subject
						</th>
						<th
							class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50"
						>
							Sender
						</th>
						<th
							class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50"
						>
							Category
						</th>
						<th
							class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50"
						>
							Amount
						</th>
						<th
							class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50"
						>
							Processed
						</th>
					</tr>
				</thead>
				<tbody>
					{#if loading}
						<tr>
							<td colspan="6" class="py-12 text-center text-text-secondary">
								<div class="flex items-center justify-center gap-2">
									<Clock size={20} class="animate-spin" />
									Loading...
								</div>
							</td>
						</tr>
					{:else if emails.length === 0}
						<tr>
							<td colspan="6" class="py-12 text-center text-text-secondary">
								<div class="flex flex-col items-center justify-center gap-3">
									<div class="bg-gray-100 p-3 rounded-full">
										<Mail size={24} class="text-gray-400" />
									</div>
									<p>No emails found.</p>
								</div>
							</td>
						</tr>
					{:else}
						{#each emails as email (email.id)}
							<tr
								class="border-b border-gray-50 last:border-0 hover:bg-gray-50/80 transition-colors"
							>
								<td class="py-3 px-4">
									{#if email.status === 'ignored'}
										<button
											on:click={() => openModal(email)}
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize shadow-sm {getStatusColor(
												email.status
											)} cursor-pointer hover:opacity-80 transition-opacity"
											title="Click to forward and create rule"
										>
											<svelte:component this={getStatusIcon(email.status)} size={12} class="mr-1" />
											{email.status}
										</button>
									{:else}
										<span
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize shadow-sm {getStatusColor(
												email.status
											)}"
										>
											<svelte:component this={getStatusIcon(email.status)} size={12} class="mr-1" />
											{email.status}
										</span>
									{/if}
								</td>
								<td class="py-3 px-4 font-medium text-text-main">
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
									{email.category || '-'}
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

		<!-- Pagination -->
		{#if pagination.total_pages > 1}
			<div class="flex items-center justify-between px-4 py-3 border-t border-gray-100">
				<div class="text-sm text-text-secondary">
					Page {pagination.page} of {pagination.total_pages} ({pagination.total} total)
				</div>
				<div class="flex gap-2">
					<button
						on:click={() => goToPage(pagination.page - 1)}
						disabled={pagination.page === 1}
						class="btn btn-secondary btn-sm"
					>
						<ChevronLeft size={16} />
						Previous
					</button>
					<button
						on:click={() => goToPage(pagination.page + 1)}
						disabled={pagination.page === pagination.total_pages}
						class="btn btn-secondary btn-sm"
					>
						Next
						<ChevronRight size={16} />
					</button>
				</div>
			</div>
		{/if}
	</div>
{:else if activeTab === 'runs'}
	<!-- Processing Runs -->
	<div class="card">
		<div class="flex items-center gap-2 mb-6 pb-4 border-b border-gray-100">
			<div class="p-2 bg-purple-50 text-purple-600 rounded-lg">
				<HistoryIcon size={20} />
			</div>
			<h3 class="text-lg font-bold text-text-main m-0">Recent Processing Runs</h3>
		</div>

		<div class="space-y-4">
			{#if runs.length === 0}
				<div class="py-12 text-center text-text-secondary">
					<div class="flex flex-col items-center justify-center gap-3">
						<div class="bg-gray-100 p-3 rounded-full">
							<HistoryIcon size={24} class="text-gray-400" />
						</div>
						<p>No processing runs found.</p>
					</div>
				</div>
			{:else}
				{#each runs as run (run.run_time)}
					<div
						class="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-primary transition-colors"
					>
						<div class="flex items-center justify-between mb-3">
							<div class="flex items-center gap-2">
								<Clock size={16} class="text-primary" />
								<span class="font-semibold text-text-main">
									{formatDate(run.run_time)}
								</span>
							</div>
							<div class="text-sm text-text-secondary">
								{run.total_emails} email{run.total_emails !== 1 ? 's' : ''}
							</div>
						</div>

						<div class="grid grid-cols-3 gap-4">
							<div class="flex items-center gap-2">
								<CheckCircle size={16} class="text-emerald-600" />
								<div>
									<div class="text-sm text-text-secondary">Forwarded</div>
									<div class="font-semibold text-emerald-600">{run.forwarded}</div>
								</div>
							</div>
							<div class="flex items-center gap-2">
								<XCircle size={16} class="text-gray-600" />
								<div>
									<div class="text-sm text-text-secondary">Blocked</div>
									<div class="font-semibold text-gray-600">{run.blocked}</div>
								</div>
							</div>
							<div class="flex items-center gap-2">
								<AlertCircle size={16} class="text-red-600" />
								<div>
									<div class="text-sm text-text-secondary">Errors</div>
									<div class="font-semibold text-red-600">{run.errors}</div>
								</div>
							</div>
						</div>
					</div>
				{/each}
			{/if}
		</div>
	</div>
{/if}

<!-- Modal for confirming toggle action -->
{#if showModal && selectedEmail}
	<div
		class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
		on:click={closeModal}
		role="dialog"
		aria-modal="true"
		aria-labelledby="modal-title"
		aria-describedby="modal-description"
	>
		<div
			class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6"
			on:click={(e) => e.stopPropagation()}
		>
			<!-- Modal Header -->
			<div class="flex items-center justify-between mb-4">
				<h3 id="modal-title" class="text-lg font-bold text-text-main">Forward Ignored Email</h3>
				<button
					on:click={closeModal}
					class="p-1 hover:bg-gray-100 rounded-lg transition-colors"
					title="Close"
					aria-label="Close modal"
				>
					<X size={20} class="text-text-secondary" />
				</button>
			</div>

			<!-- Success Message -->
			{#if successMessage}
				<div class="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-start gap-2">
					<CheckCircle size={20} class="text-emerald-600 flex-shrink-0 mt-0.5" />
					<p class="text-sm text-emerald-800">{successMessage}</p>
				</div>
			{/if}

			<!-- Error Message -->
			{#if errorMessage}
				<div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
					<AlertCircle size={20} class="text-red-600 flex-shrink-0 mt-0.5" />
					<p class="text-sm text-red-800">{errorMessage}</p>
				</div>
			{/if}

			<!-- Modal Content -->
			<div class="mb-6">
				<p id="modal-description" class="text-text-secondary mb-4">
					This email was marked as ignored. Do you want to forward it and create a rule to
					automatically forward similar emails in the future?
				</p>

				<div class="bg-gray-50 rounded-lg p-4 space-y-2">
					<div>
						<span class="text-xs font-semibold text-text-secondary uppercase">Subject:</span>
						<p class="text-sm text-text-main break-words">{selectedEmail.subject}</p>
					</div>
					<div>
						<span class="text-xs font-semibold text-text-secondary uppercase">Sender:</span>
						<p class="text-sm text-text-main break-words">{selectedEmail.sender}</p>
					</div>
					{#if selectedEmail.reason}
						<div>
							<span class="text-xs font-semibold text-text-secondary uppercase">Reason:</span>
							<p class="text-sm text-text-main">{selectedEmail.reason}</p>
						</div>
					{/if}
				</div>
			</div>

			<!-- Modal Actions -->
			<div class="flex gap-3 justify-end">
				<button 
					on:click={closeModal} 
					class="btn btn-secondary"
					disabled={isProcessing}
				> 
					Cancel 
				</button>
				<button 
					on:click={confirmToggle} 
					class="btn btn-primary"
					disabled={isProcessing}
				>
					{#if isProcessing}
						<RefreshCw size={16} class="animate-spin" />
						Processing...
					{:else}
						<RefreshCw size={16} />
						Forward & Create Rule
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}
