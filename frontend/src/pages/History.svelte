<script lang="ts">
	import { fetchJson } from '../lib/api';
	import { SvelteURLSearchParams } from 'svelte/reactivity';
	import { onMount } from 'svelte';
	import CategoryEditModal from '../components/CategoryEditModal.svelte';
	import HistoryStats from '../components/HistoryStats.svelte';
	import HistoryFilters from '../components/HistoryFilters.svelte';
	import HistoryTable from '../components/HistoryTable.svelte';
	import HistoryMobileView from '../components/HistoryMobileView.svelte';
	import ProcessingRunsList from '../components/ProcessingRunsList.svelte';
	import EmailDetailsModal from '../components/EmailDetailsModal.svelte';
	import { CheckCircle, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-svelte';

	// Constants
	const SUCCESS_MESSAGE_DELAY = 1500; // milliseconds
	const FEEDBACK_MESSAGE_DELAY = 2000; // milliseconds

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

	let emails = $state<Email[]>([]);
	let runs = $state<Run[]>([]);
	let stats = $state({
		total: 0,
		forwarded: 0,
		blocked: 0,
		errors: 0,
		total_amount: 0,
		status_breakdown: {} as Record<string, number>
	});

	let pagination = $state({
		page: 1,
		per_page: 50,
		total: 0,
		total_pages: 0
	});

	let filters = $state({
		status: '',
		date_from: '',
		date_to: '',
		sender: '',
		min_amount: '',
		max_amount: ''
	});

	let loading = $state(true);
	let activeTab = $state<'emails' | 'runs'>('emails');
	let showModal = $state(false);
	let selectedEmail = $state<Email | null>(null);
	let isProcessing = $state(false);
	let isAnalyzing = $state(false);
	let selectedAnalysis = $state<AnalysisOutcome | null>(null);
	let successMessage = $state('');
	let errorMessage = $state('');
	let showCategoryEditModal = $state(false);
	let categoryEditEmail = $state<{
		id: number;
		category: string;
		sender: string;
		subject: string;
	} | null>(null);

	async function loadHistory() {
		loading = true;
		try {
			const params = new SvelteURLSearchParams({
				page: pagination.page.toString(),
				per_page: pagination.per_page.toString()
			});

			if (filters.status) params.append('status', filters.status);
			if (filters.date_from) params.append('date_from', filters.date_from);
			if (filters.date_to) params.append('date_to', filters.date_to);
			if (filters.sender) params.append('sender', filters.sender);
			if (filters.min_amount) params.append('min_amount', filters.min_amount);
			if (filters.max_amount) params.append('max_amount', filters.max_amount);

			const [historyRes, statsRes, runsRes] = await Promise.all([
				fetchJson(`/history/emails?${params}`),
				fetchJson('/history/stats'),
				fetchJson('/history/runs')
			]);

			emails = historyRes.emails ?? [];
			pagination = historyRes.pagination ?? { page: 1, per_page: 50, total: 0, total_pages: 0 };
			stats = statsRes ?? {
				total: 0,
				forwarded: 0,
				blocked: 0,
				errors: 0,
				total_amount: 0,
				status_breakdown: {}
			};
			runs = runsRes.runs ?? [];
		} catch (e) {
			console.error('Failed to load history', e);
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadHistory();
	});

	function handleFilterChange() {
		pagination.page = 1;
		loadHistory();
	}

	function handleClearFilters() {
		filters = {
			status: '',
			date_from: '',
			date_to: '',
			sender: '',
			min_amount: '',
			max_amount: ''
		};
		handleFilterChange();
	}

	function goToPage(page: number) {
		pagination.page = page;
		loadHistory();
	}

	function openModal(email: Email) {
		selectedEmail = email;
		showModal = true;
		successMessage = '';
		errorMessage = '';
	}

	function openModalAndAnalyze(email: Email) {
		selectedEmail = email;
		showModal = true;
		reprocessEmail(email.id);
	}

	function closeModal() {
		showModal = false;
		selectedEmail = null;
		selectedAnalysis = null;
		successMessage = '';
		errorMessage = '';
		isProcessing = false;
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
			}, SUCCESS_MESSAGE_DELAY);
		} catch (e) {
			console.error('Toggle failed', e);
			errorMessage = 'Failed to toggle email status.';
		} finally {
			isProcessing = false;
		}
	}

	async function confirmToggleToIgnored() {
		if (!selectedEmail || isProcessing) return;

		isProcessing = true;
		errorMessage = '';
		successMessage = '';

		try {
			const result = await fetchJson('/actions/toggle-to-ignored', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email_id: selectedEmail.id })
			});

			successMessage = result.message || 'Email status changed to ignored successfully!';

			// Wait a moment to show success message, then close and reload
			setTimeout(async () => {
				closeModal();
				await loadHistory();
			}, SUCCESS_MESSAGE_DELAY);
		} catch (e) {
			console.error('Toggle to ignored failed', e);
			errorMessage = 'Failed to change email status to ignored.';
		} finally {
			isProcessing = false;
		}
	}

	async function reprocessEmail(emailId: number) {
		if (!selectedEmail) return;
		isAnalyzing = true;
		errorMessage = '';
		try {
			selectedAnalysis = await fetchJson(`/history/reprocess/${emailId}`, {
				method: 'POST'
			});
		} catch (e) {
			console.error('Failed to analyze email', e);
			errorMessage = 'Retrospective analysis failed. Content may have expired.';
		} finally {
			isAnalyzing = false;
		}
	}

	function openCategoryEditModal(email: Email) {
		categoryEditEmail = {
			id: email.id,
			category: email.category || 'other',
			sender: email.sender,
			subject: email.subject
		};
		showCategoryEditModal = true;
	}

	function closeCategoryEditModal() {
		showCategoryEditModal = false;
		categoryEditEmail = null;
	}

	function handleCategoryUpdateSuccess() {
		loadHistory();
	}

	async function submitFeedback(isReceipt: boolean) {
		if (!selectedEmail) return;
		isProcessing = true;
		try {
			await fetchJson('/history/feedback', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email_id: selectedEmail.id, is_receipt: isReceipt })
			});
			successMessage = 'Feedback recorded. A rule has been suggested in Shadow Mode.';
			setTimeout(() => {
				closeModal();
				loadHistory();
			}, FEEDBACK_MESSAGE_DELAY);
		} catch (e) {
			console.error('Failed to submit feedback', e);
			errorMessage = 'Failed to submit feedback.';
		} finally {
			isProcessing = false;
		}
	}

	async function exportToCSV() {
		// Build URL with current filters
		const params = new SvelteURLSearchParams({ format: 'csv' });
		if (filters.status) params.append('status', filters.status);
		if (filters.date_from) params.append('date_from', filters.date_from);
		if (filters.date_to) params.append('date_to', filters.date_to);
		if (filters.sender) params.append('sender', filters.sender);
		if (filters.min_amount) params.append('min_amount', filters.min_amount);
		if (filters.max_amount) params.append('max_amount', filters.max_amount);

		const url = `/api/history/export?${params.toString()}`;

		// Fetch CSV first so we can handle errors and provide user feedback
		errorMessage = '';
		successMessage = 'Exporting history...';
		try {
			const response = await fetch(url, { method: 'GET' });
			if (!response.ok) {
				throw new Error(`Export failed with status ${response.status}`);
			}

			const blob = await response.blob();
			const downloadUrl = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = downloadUrl;
			// Generate filename with current date like the backend does
			const date = new Date().toISOString().split('T')[0];
			a.download = `expenses_${date}.csv`;
			document.body.appendChild(a);
			a.click();
			a.remove();
			URL.revokeObjectURL(downloadUrl);
			successMessage = 'Export successful!';
			setTimeout(() => {
				if (successMessage === 'Export successful!') successMessage = '';
			}, 3000);
		} catch (e) {
			console.error('Failed to export history as CSV', e);
			errorMessage = 'Failed to export history. Please try again.';
			successMessage = '';
		}
	}
</script>

<div class="mb-8">
	<h2 class="text-2xl font-bold text-text-main mb-1">History</h2>
	<p class="text-text-secondary text-sm">
		Complete history of email processing and automated runs.
	</p>
</div>

<!-- Global Alerts -->
{#if !showModal}
	{#if successMessage}
		<div
			class="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-start gap-3 animate-in fade-in slide-in-from-top-4 duration-300"
		>
			<CheckCircle size={24} class="text-emerald-600 shrink-0" />
			<p class="text-emerald-800 font-medium">{successMessage}</p>
		</div>
	{/if}
	{#if errorMessage}
		<div
			class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3 animate-in fade-in slide-in-from-top-4 duration-300"
		>
			<AlertCircle size={24} class="text-red-600 shrink-0" />
			<p class="text-red-800 font-medium">{errorMessage}</p>
		</div>
	{/if}
{/if}

<!-- Stats Cards -->
<HistoryStats {stats} />

<!-- Tabs -->
<div class="flex gap-2 mb-6 border-b border-gray-200">
	<button
		class="px-4 py-2 font-medium transition-all {activeTab === 'emails'
			? 'text-primary border-b-2 border-primary'
			: 'text-text-secondary hover:text-text-main'}"
		onclick={() => (activeTab = 'emails')}
	>
		All Emails
	</button>
	<button
		class="px-4 py-2 font-medium transition-all {activeTab === 'runs'
			? 'text-primary border-b-2 border-primary'
			: 'text-text-secondary hover:text-text-main'}"
		onclick={() => (activeTab = 'runs')}
	>
		Processing Runs
	</button>
</div>

{#if activeTab === 'emails'}
	<!-- Filters -->
	<HistoryFilters
		bind:filters
		{pagination}
		{loading}
		onFilterChange={handleFilterChange}
		onClearFilters={handleClearFilters}
		onExport={exportToCSV}
	/>

	<!-- Email History Table (Desktop) -->
	<HistoryTable
		{emails}
		{loading}
		onEmailClick={openModal}
		onAnalyzeClick={openModalAndAnalyze}
		onCategoryEditClick={openCategoryEditModal}
	/>

	<!-- Email History Cards (Mobile) -->
	<HistoryMobileView
		{emails}
		{loading}
		onEmailClick={openModal}
		onAnalyzeClick={openModalAndAnalyze}
		onCategoryEditClick={openCategoryEditModal}
	/>
	<!-- Pagination -->
	{#if pagination.total_pages > 1}
		<div
			class="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-700"
		>
			<div class="text-sm text-text-secondary dark:text-text-secondary-dark">
				Page {pagination.page} of {pagination.total_pages} ({pagination.total} total)
			</div>
			<div class="flex gap-2">
				<button
					onclick={() => goToPage(pagination.page - 1)}
					disabled={pagination.page === 1}
					class="btn btn-secondary btn-sm"
				>
					<ChevronLeft size={16} />
					Previous
				</button>
				<button
					onclick={() => goToPage(pagination.page + 1)}
					disabled={pagination.page === pagination.total_pages}
					class="btn btn-secondary btn-sm"
				>
					Next
					<ChevronRight size={16} />
				</button>
			</div>
		</div>
	{/if}
{:else if activeTab === 'runs'}
	<!-- Processing Runs -->
	<ProcessingRunsList {runs} />
{/if}

<!-- Modal for confirming toggle action -->
<EmailDetailsModal
	isOpen={showModal}
	{selectedEmail}
	{isProcessing}
	{isAnalyzing}
	{selectedAnalysis}
	{successMessage}
	{errorMessage}
	onClose={closeModal}
	onConfirmToggle={confirmToggle}
	onConfirmToggleToIgnored={confirmToggleToIgnored}
	onSubmitFeedback={submitFeedback}
/>

<!-- Category Edit Modal -->
{#if categoryEditEmail}
	<CategoryEditModal
		bind:isOpen={showCategoryEditModal}
		emailId={categoryEditEmail.id}
		currentCategory={categoryEditEmail.category}
		sender={categoryEditEmail.sender}
		subject={categoryEditEmail.subject}
		onClose={closeCategoryEditModal}
		onSuccess={handleCategoryUpdateSuccess}
	/>
{/if}
