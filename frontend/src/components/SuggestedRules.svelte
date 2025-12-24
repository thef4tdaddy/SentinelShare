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
			const res = await api.learning.getCandidates();
			candidates = Array.isArray(res) ? res : [];
		} catch (e) {
			console.error('Failed to load suggestions', e);
			candidates = [];
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
			candidates = Array.isArray(candidates) ? candidates.filter((c) => c.id !== candidate.id) : [];
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
			candidates = Array.isArray(candidates) ? candidates.filter((c) => c.id !== candidate.id) : [];
		} catch (e) {
			console.error('Failed to ignore', e);
		} finally {
			processingId = null;
		}
	}

	onMount(loadCandidates);
</script>

<div class="bg-indigo-50/30 rounded-xl p-6 mb-8 border-2 border-primary/20 shadow-xs">
	<div class="flex justify-between items-center mb-5">
		<h2 class="text-xl font-medium text-primary flex items-center gap-3">
			<span class="p-1.5 bg-primary/10 rounded-lg text-primary">✨</span>
			<span class="tracking-tight">Suggested Rules</span>
			{#if candidates.length > 0}
				<span
					class="bg-primary text-white text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider"
					>{candidates.length}</span
				>
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
		<div class="text-primary/40 py-8 text-center text-sm font-medium animate-pulse">
			Discovering matching patterns...
		</div>
	{:else if !Array.isArray(candidates) || candidates.length === 0}
		<div
			class="text-text-secondary/60 py-8 text-center text-sm bg-white/50 rounded-lg border border-dashed border-gray-200"
		>
			No suggestions found. Try scanning your history for missed receipts.
		</div>
	{:else}
		<div class="space-y-4">
			{#each candidates as candidate (candidate.id)}
				<div
					class="bg-white border border-primary/10 rounded-xl p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-5 transition-all hover:shadow-md hover:border-primary/20 group"
				>
					<div class="flex-1">
						<div class="flex items-center gap-2 mb-2">
							<span
								class="font-mono text-sm text-primary font-medium bg-primary/5 px-2.5 py-0.5 rounded-md border border-primary/10"
							>
								{candidate.sender}
							</span>
							{#if candidate.matches > 1}
								<span
									class="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-100 uppercase tracking-tight"
								>
									{candidate.matches} matches
								</span>
							{/if}
						</div>

						{#if candidate.subject_pattern}
							<div class="text-sm text-primary/80 font-normal">
								Subject matches: <span class="font-mono text-primary font-semibold"
									>{candidate.subject_pattern}</span
								>
							</div>
						{/if}

						{#if candidate.example_subject}
							<div class="text-xs text-text-secondary/70 mt-1.5 italic font-light">
								Recent: "{candidate.example_subject}"
							</div>
						{/if}
					</div>

					<div class="flex gap-3 shrink-0">
						<button
							on:click={() => ignore(candidate)}
							disabled={processingId === candidate.id}
							class="px-4 py-2 text-sm text-text-secondary hover:text-primary hover:bg-gray-50 rounded-lg transition-all disabled:opacity-50 font-medium"
						>
							Ignore
						</button>
						<button
							on:click={() => approve(candidate)}
							disabled={processingId === candidate.id}
							class="btn btn-accent px-5 py-2 text-sm shadow-sm hover:shadow active:scale-95 flex items-center gap-2"
						>
							{#if processingId === candidate.id}
								<span class="animate-pulse">Adding...</span>
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
