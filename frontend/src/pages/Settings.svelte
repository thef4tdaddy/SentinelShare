<script lang="ts">
	import PreferenceList from '../components/PreferenceList.svelte';
	import EmailTemplateEditor from '../components/EmailTemplateEditor.svelte';
	import ConfirmDialog from '../components/ConfirmDialog.svelte';
	import { fetchJson } from '../lib/api';
	import { toasts } from '../lib/stores/toast';
	import { theme as themeStore } from '../lib/stores/theme';
	import {
		Play,
		Settings,
		Sliders,
		Mail,
		CheckCircle,
		AlertTriangle,
		Loader2,
		History as HistoryIcon,
		Moon,
		Sun
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

	// Reactive theme value using $derived
	const currentTheme = $derived($themeStore);

	function toggleTheme() {
		themeStore.toggle();
	}

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
		<p class="text-text-secondary text-sm dark:text-text-secondary-dark">Manage detection rules and preferences.</p>
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
	<section>
		<h3 class="text-lg font-bold text-text-main mb-4 dark:text-text-main-dark">Appearance</h3>
		<div class="card">
			<div class="flex items-center justify-between">
				<div>
					<p class="font-medium text-text-main dark:text-text-main-dark">Dark Mode</p>
					<p class="text-sm text-text-secondary dark:text-text-secondary-dark">
						Toggle between light and dark theme
					</p>
				</div>
				<button
					onclick={toggleTheme}
					class="btn btn-secondary flex items-center gap-2"
					aria-label="Toggle theme"
				>
					{#if currentTheme === 'dark'}
						<Sun size={18} />
						Light
					{:else}
						<Moon size={18} />
						Dark
					{/if}
				</button>
			</div>
		</div>
	</section>
	<!-- Connection Status -->
	<section>
		<h3 class="text-lg font-bold text-text-main mb-4 dark:text-text-main-dark">Inbox Status</h3>
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
			{#each connectionResults as res (res.account)}
				<div
					class="card flex items-center justify-between p-4 {res.success
						? 'border-l-4 border-l-green-500 dark:border-l-green-400'
						: 'border-l-4 border-l-red-500 dark:border-l-red-400'}"
				>
					<div class="overflow-hidden">
						<p class="font-medium text-text-main truncate dark:text-text-main-dark" title={res.account}>{res.account}</p>
						<p class="text-xs {res.success ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
							{res.success ? 'Connected' : 'Connection Failed'}
						</p>
					</div>
					<div>
						{#if res.success}
							<CheckCircle class="text-green-500 dark:text-green-400" size={20} />
						{:else}
							<div class="group relative">
								<AlertTriangle class="text-red-500 cursor-help dark:text-red-400" size={20} />
								<div
									class="absolute right-0 top-6 w-48 p-2 bg-gray-800 text-white text-xs rounded shadow-lg z-10 hidden group-hover:block dark:bg-gray-700"
								>
									{res.error}
								</div>
							</div>
						{/if}
					</div>
				</div>
			{:else}
				<div class="text-text-secondary text-sm italic dark:text-text-secondary-dark">
					No accounts configured or check pending...
				</div>
			{/each}
		</div>
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
			<h3 class="text-lg font-bold text-text-main dark:text-text-main-dark">Detection Preferences</h3>
		</div>
		<PreferenceList type="preferences" />
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
