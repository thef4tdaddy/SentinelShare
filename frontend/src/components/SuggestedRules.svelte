<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type LearningCandidate } from '../lib/api';

	export let onRuleAdded: () => void; // Callback when a rule is created

	let candidates: LearningCandidate[] = [];
	let loading = false;
	let processingId: number | null = null;
	let scanLoading = false;

	async function loadCandidates() {
		loading = true;
		try {
			candidates = await api.learning.getCandidates();
		} catch (e) {
			console.error('Failed to load suggestions', e);
		} finally {
			loading = false;
		}
	}

	async function runScan() {
		scanLoading = true;
		try {
			await api.learning.scan(30);
			// Scan is background task, but we can poll or just wait a bit and reload
			// Ideally backend returns immediately. We should give it a moment or tell user it's running.
			// For now, let's just reload after 2 seconds to see if anything appeared quickly
			setTimeout(loadCandidates, 2000);
		} catch (e) {
			console.error('Scan trigger failed', e);
		} finally {
			scanLoading = false;
		}
	}

	async function approve(candidate: LearningCandidate) {
		processingId = candidate.id;
		try {
			await api.learning.approve(candidate.id);
			candidates = candidates.filter((c) => c.id !== candidate.id);
			onRuleAdded();
		} catch (e) {
			console.error('Failed to approve', e);
			alert('Failed to create rule');
		} finally {
			processingId = null;
		}
	}

	async function ignore(candidate: LearningCandidate) {
		processingId = candidate.id;
		try {
			await api.learning.ignore(candidate.id);
			candidates = candidates.filter((c) => c.id !== candidate.id);
		} catch (e) {
			console.error('Failed to ignore', e);
		} finally {
			processingId = null;
		}
	}

	onMount(loadCandidates);
</script>

<div class="bg-gray-800 rounded-lg p-6 mb-6 border border-gray-700">
	<div class="flex justify-between items-center mb-4">
		<h2 class="text-xl font-semibold text-white flex items-center gap-2">
			<span>✨ Suggested Rules</span>
			{#if candidates.length > 0}
				<span class="bg-blue-600 text-xs px-2 py-1 rounded-full">{candidates.length}</span>
			{/if}
		</h2>
		<div class="flex gap-2">
			<button
				on:click={loadCandidates}
				class="p-2 text-gray-400 hover:text-white rounded transition-colors"
				title="Refresh"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
						clip-rule="evenodd"
					/>
				</svg>
			</button>
			<button
				on:click={runScan}
				disabled={scanLoading}
				class="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2"
			>
				{#if scanLoading}
					<svg
						class="animate-spin h-4 w-4 text-white"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
					>
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					Scanning...
				{:else}
					Scan for Missed
				{/if}
			</button>
		</div>
	</div>

	{#if loading}
		<div class="text-gray-400 py-4 text-center">Loading suggestions...</div>
	{:else if candidates.length === 0}
		<div class="text-gray-500 py-4 text-center text-sm">
			No suggestions found. Try scanning your history for missed receipts.
		</div>
	{:else}
		<div class="space-y-3">
			{#each candidates as candidate (candidate.id)}
				<div
					class="bg-gray-750 border border-gray-600 rounded-md p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition-all hover:border-gray-500"
				>
					<div class="flex-1">
						<div class="flex items-center gap-2 mb-1">
							<span class="font-mono text-sm text-yellow-400 bg-yellow-900/30 px-2 rounded">
								{candidate.sender}
							</span>
							{#if candidate.matches > 1}
								<span class="text-xs text-green-400 bg-green-900/30 px-2 rounded-full">
									Matches {candidate.matches} emails
								</span>
							{/if}
						</div>

						{#if candidate.subject_pattern}
							<div class="text-sm text-gray-300">
								Subject matches: <span class="font-mono text-gray-200"
									>{candidate.subject_pattern}</span
								>
							</div>
						{/if}

						{#if candidate.example_subject}
							<div class="text-xs text-gray-500 mt-1 italic">
								Ex: "{candidate.example_subject}"
							</div>
						{/if}
					</div>

					<div class="flex gap-2">
						<button
							on:click={() => ignore(candidate)}
							disabled={processingId === candidate.id}
							class="px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors disabled:opacity-50"
						>
							Ignore
						</button>
						<button
							on:click={() => approve(candidate)}
							disabled={processingId === candidate.id}
							class="px-3 py-1.5 text-sm bg-green-600 hover:bg-green-700 text-white rounded font-medium transition-colors shadow-sm disabled:opacity-50 flex items-center gap-1"
						>
							{#if processingId === candidate.id}
								...
							{:else}
								Add Rule
							{/if}
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
