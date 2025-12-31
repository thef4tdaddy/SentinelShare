<script lang="ts">
	import PreferenceList from '../components/PreferenceList.svelte';
	import EmailTemplateEditor from '../components/EmailTemplateEditor.svelte';
	import AccountList from '../components/settings/AccountList.svelte';
	import InboxStatus from '../components/settings/InboxStatus.svelte';
	import AppearanceSettings from '../components/settings/AppearanceSettings.svelte';
	import CategoryRulesList from '../components/CategoryRulesList.svelte';
	import ConfirmDialog from '../components/ConfirmDialog.svelte';
	import { fetchJson } from '../lib/api';
	import { toasts } from '../lib/stores/toast';
	import {
		Play,
		Settings,
		Sliders,
		Loader2,
		History as HistoryIcon,
		User,
		Tag,
		Mail
	} from 'lucide-svelte';
	import { onMount, onDestroy } from 'svelte';

	interface ConnectionResult {
		account: string;
		success: boolean;
		error?: string;
	}

	let loading = $state(false);
	let connectionResults: ConnectionResult[] = $state([]);
	let checkingConnections = $state(false);
	let pollInterval: ReturnType<typeof setInterval>;
	let showConfirmDialog = $state(false);
	let showDeleteDialog = $state(false);
	let accountToDelete: { id: number; email: string; onComplete: () => void } | null = $state(null);

	// Reactive theme value using $derived
	// Moved to AppearanceSettings
	// const currentTheme = $derived($themeStore);

	// function toggleTheme() {
	// 	themeStore.toggle();
	// }

	function openConfirmDialog() {
		showConfirmDialog = true;
	}

	async function handleConfirmPoll() {
		showConfirmDialog = false;
		try {
			loading = true;
			const res = await fetchJson('/settings/trigger-poll', { method: 'POST' });
			toasts.trigger(res.message || 'Poll triggered', 'success');
		} catch {
			toasts.trigger('Error triggering poll', 'error');
		} finally {
			loading = false;
		}
	}

	function handleCancelPoll() {
		showConfirmDialog = false;
	}

	function handleDeleteAccountRequest(id: number, email: string, onComplete: () => void) {
		accountToDelete = { id, email, onComplete };
		showDeleteDialog = true;
	}

	async function handleConfirmDelete() {
		if (!accountToDelete) return;

		showDeleteDialog = false;
		try {
			await fetchJson(`/settings/accounts/${accountToDelete.id}`, { method: 'DELETE' });
			toasts.trigger('Account deleted', 'success');
			// Call the completion callback to reload the accounts list
			accountToDelete.onComplete();
		} catch {
			toasts.trigger('Failed to delete account', 'error');
		} finally {
			accountToDelete = null;
		}
	}

	function handleCancelDelete() {
		showDeleteDialog = false;
		accountToDelete = null;
	}

	async function reprocessAllIgnored() {
		if (!confirm('Reprocess all ignored emails from last 24h?')) return;
		loading = true;
		try {
			const res = await fetchJson('/api/history/reprocess-all-ignored', { method: 'POST' });
			toasts.trigger(res.message, 'success');
		} catch {
			toasts.trigger('Failed to reprocess emails', 'error');
		} finally {
			loading = false;
		}
	}

	async function checkConnections() {
		checkingConnections = true;
		try {
			connectionResults = await fetchJson('/settings/test-connections', { method: 'POST' });
		} catch (e) {
			console.error('Failed to test connections', e);
		} finally {
			checkingConnections = false;
		}
	}

	onMount(() => {
		checkConnections();
		// Poll status every 30 seconds
		pollInterval = setInterval(checkConnections, 30000);
	});

	onDestroy(() => {
		if (pollInterval) clearInterval(pollInterval);
	});
</script>

<div class="mb-8 flex items-center justify-between">
	<div>
		<h2 class="text-2xl font-bold text-text-main mb-1 dark:text-text-main-dark">Settings</h2>
		<p class="text-text-secondary text-sm dark:text-text-secondary-dark">
			Manage detection rules and preferences.
		</p>
	</div>

	<div class="flex gap-2">
		<button onclick={checkConnections} disabled={checkingConnections} class="btn btn-secondary">
			<Loader2 size={16} class={checkingConnections ? 'animate-spin' : ''} />
			{checkingConnections ? 'Testing...' : 'Test Connections'}
		</button>
		<button onclick={reprocessAllIgnored} disabled={loading} class="btn btn-secondary">
			<HistoryIcon size={16} class={loading ? 'animate-spin' : ''} />
			Reprocess Ignored
		</button>
		<button onclick={openConfirmDialog} disabled={loading} class="btn btn-primary">
			<Play size={16} class={loading ? 'animate-spin' : ''} />
			{loading ? 'Running...' : 'Run Now'}
		</button>
	</div>
</div>

<div class="space-y-8">
	<!-- Theme Toggle Section -->
	<!-- Theme Toggle Section -->
	<AppearanceSettings />
	<!-- Connection Status -->
	<InboxStatus results={connectionResults} />

	<!-- Email Accounts Management Section -->
	<section>
		<div class="flex items-center gap-2 mb-4">
			<User size={20} class="text-text-secondary" />
			<h3 class="text-lg font-bold text-text-main">Email Accounts</h3>
		</div>
		<AccountList onDeleteRequest={handleDeleteAccountRequest} />
	</section>

	<!-- Email Template Section -->
	<section>
		<div class="flex items-center gap-2 mb-4">
			<Mail size={20} class="text-text-secondary dark:text-text-secondary-dark" />
			<h3 class="text-lg font-bold text-text-main dark:text-text-main-dark">Email Template</h3>
		</div>
		<EmailTemplateEditor />
	</section>

	<!-- Preferences Section -->
	<section>
		<div class="flex items-center gap-2 mb-4">
			<Sliders size={20} class="text-text-secondary dark:text-text-secondary-dark" />
			<h3 class="text-lg font-bold text-text-main dark:text-text-main-dark">
				Detection Preferences
			</h3>
		</div>
		<PreferenceList type="preferences" />
	</section>

	<!-- Category Rules Section -->
	<section>
		<div class="flex items-center gap-2 mb-4">
			<Tag size={20} class="text-text-secondary dark:text-text-secondary-dark" />
			<h3 class="text-lg font-bold text-text-main dark:text-text-main-dark">Category Rules</h3>
		</div>
		<CategoryRulesList />
	</section>

	<!-- Rules Section -->
	<section>
		<div class="flex items-center gap-2 mb-4">
			<Settings size={20} class="text-text-secondary dark:text-text-secondary-dark" />
			<h3 class="text-lg font-bold text-text-main dark:text-text-main-dark">Manual Rules</h3>
		</div>
		<PreferenceList type="rules" />
	</section>
</div>

<ConfirmDialog
	bind:isOpen={showConfirmDialog}
	onConfirm={handleConfirmPoll}
	onCancel={handleCancelPoll}
	title="Run Email Check"
	message="Do you want to run the email check now? This will process all emails from your configured accounts."
	confirmText="Run Now"
	cancelText="Cancel"
/>

<ConfirmDialog
	bind:isOpen={showDeleteDialog}
	onConfirm={handleConfirmDelete}
	onCancel={handleCancelDelete}
	title="Delete Email Account"
	message={accountToDelete
		? `Are you sure you want to delete the account "${accountToDelete.email}"? This action cannot be undone.`
		: 'Delete this account?'}
	confirmText="Delete"
	cancelText="Cancel"
/>
