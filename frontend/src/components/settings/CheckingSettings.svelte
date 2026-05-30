<script lang="ts">
	import { Play, Pause } from 'lucide-svelte';
	import { fetchJson } from '../../lib/api';
	import { toasts } from '../../lib/stores/toast';
	import { onMount } from 'svelte';

	let checkingDisabled = $state(false);
	let loading = $state(false);

	async function fetchCheckingStatus() {
		try {
			const res = await fetchJson('/settings/disable-checking');
			checkingDisabled = res.disabled;
		} catch (e) {
			console.error('Failed to fetch checking status', e);
		}
	}

	async function toggleCheckingStatus() {
		loading = true;
		try {
			const res = await fetchJson('/settings/disable-checking', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ disabled: !checkingDisabled })
			});
			checkingDisabled = res.disabled;
			toasts.trigger(
				checkingDisabled ? 'Email checking disabled globally' : 'Email checking enabled globally',
				'success'
			);
		} catch {
			toasts.trigger('Failed to update checking status', 'error');
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		fetchCheckingStatus();
	});
</script>

<section>
	<h3 class="text-lg font-bold text-text-main mb-4 dark:text-text-main-dark">
		Email Checking Status
	</h3>
	<div class="card">
		<div class="flex items-center justify-between">
			<div>
				<p class="font-medium text-text-main dark:text-text-main-dark flex items-center gap-2">
					{#if checkingDisabled}
						<span class="inline-flex h-2.5 w-2.5 rounded-full bg-red-500"></span>
						Disabled
					{:else}
						<span class="inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
						Active
					{/if}
				</p>
				<p class="text-sm text-text-secondary dark:text-text-secondary-dark mt-1">
					{#if checkingDisabled}
						SentinelShare is currently paused. No emails will be fetched or processed.
					{:else}
						SentinelShare is actively monitoring and processing incoming emails in the background.
					{/if}
				</p>
			</div>
			<button
				onclick={toggleCheckingStatus}
				disabled={loading}
				class="btn {checkingDisabled ? 'btn-primary' : 'btn-secondary'} flex items-center gap-2"
				aria-label="Toggle email checking"
			>
				{#if checkingDisabled}
					<Play size={18} />
					Enable Checking
				{:else}
					<Pause size={18} />
					Disable Checking
				{/if}
			</button>
		</div>
	</div>
</section>
