<script lang="ts">
	import PreferenceList from '../components/PreferenceList.svelte';
	import EmailTemplateEditor from '../components/EmailTemplateEditor.svelte';
	import ConfirmDialog from '../components/ConfirmDialog.svelte';
	import { fetchJson } from '../lib/api';
	import {
		Play,
		Settings,
		Sliders,
		Mail,
		CheckCircle,
		AlertTriangle,
		Loader2
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

	function openConfirmDialog() {
		showConfirmDialog = true;
	}

	async function handleConfirmPoll() {
		showConfirmDialog = false;
		try {
			loading = true;
			const res = await fetchJson('/settings/trigger-poll', { method: 'POST' });
			alert(res.message || 'Poll triggered');
		} catch {
			alert('Error triggering poll');
		} finally {
			loading = false;
		}
	}

	function handleCancelPoll() {
		showConfirmDialog = false;
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
		<h2 class="text-2xl font-bold text-text-main mb-1">Settings</h2>
		<p class="text-text-secondary text-sm">Manage detection rules and preferences.</p>
	</div>

	<div class="flex gap-2">
		<button on:click={checkConnections} disabled={checkingConnections} class="btn btn-secondary">
			<Loader2 size={16} class={checkingConnections ? 'animate-spin' : ''} />
			{checkingConnections ? 'Testing...' : 'Test Connections'}
		</button>
		<button on:click={openConfirmDialog} disabled={loading} class="btn btn-primary">
			<Play size={16} class={loading ? 'animate-spin' : ''} />
			{loading ? 'Running...' : 'Run Now'}
		</button>
	</div>
</div>

<div class="space-y-8">
	<!-- Connection Status -->
	<section>
		<h3 class="text-lg font-bold text-text-main mb-4">Inbox Status</h3>
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
			{#each connectionResults as res (res.account)}
				<div
					class="card flex items-center justify-between p-4 {res.success
						? 'border-l-4 border-l-green-500'
						: 'border-l-4 border-l-red-500'}"
				>
					<div class="overflow-hidden">
						<p class="font-medium text-text-main truncate" title={res.account}>{res.account}</p>
						<p class="text-xs {res.success ? 'text-green-600' : 'text-red-600'}">
							{res.success ? 'Connected' : 'Connection Failed'}
						</p>
					</div>
					<div>
						{#if res.success}
							<CheckCircle class="text-green-500" size={20} />
						{:else}
							<div class="group relative">
								<AlertTriangle class="text-red-500 cursor-help" size={20} />
								<div
									class="absolute right-0 top-6 w-48 p-2 bg-gray-800 text-white text-xs rounded shadow-lg z-10 hidden group-hover:block"
								>
									{res.error}
								</div>
							</div>
						{/if}
					</div>
				</div>
			{:else}
				<div class="text-text-secondary text-sm italic">
					No accounts configured or check pending...
				</div>
			{/each}
		</div>
	</section>

	<!-- Email Template Section -->
	<section>
		<div class="flex items-center gap-2 mb-4">
			<Mail size={20} class="text-text-secondary" />
			<h3 class="text-lg font-bold text-text-main">Email Template</h3>
		</div>
		<EmailTemplateEditor />
	</section>

	<!-- Preferences Section -->
	<section>
		<div class="flex items-center gap-2 mb-4">
			<Sliders size={20} class="text-text-secondary" />
			<h3 class="text-lg font-bold text-text-main">Detection Preferences</h3>
		</div>
		<PreferenceList type="preferences" />
	</section>

	<!-- Rules Section -->
	<section>
		<div class="flex items-center gap-2 mb-4">
			<Settings size={20} class="text-text-secondary" />
			<h3 class="text-lg font-bold text-text-main">Manual Rules</h3>
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
