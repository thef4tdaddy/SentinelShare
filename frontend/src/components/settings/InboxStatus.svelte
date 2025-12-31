<script lang="ts">
	import { CheckCircle, AlertTriangle } from 'lucide-svelte';

	interface ConnectionResult {
		account: string;
		success: boolean;
		error?: string;
	}

	let { results = [] }: { results: ConnectionResult[] } = $props();
</script>

<section>
	<h3 class="text-lg font-bold text-text-main mb-4 dark:text-text-main-dark">Inbox Status</h3>
	<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
		{#each results as res (res.account)}
			<div
				class="card flex items-center justify-between p-4 {res.success
					? 'border-l-4 border-l-green-500 dark:border-l-green-400'
					: 'border-l-4 border-l-red-500 dark:border-l-red-400'}"
			>
				<div class="overflow-hidden">
					<p
						class="font-medium text-text-main truncate dark:text-text-main-dark"
						title={res.account}
					>
						{res.account}
					</p>
					<p
						class="text-xs {res.success
							? 'text-green-600 dark:text-green-400'
							: 'text-red-600 dark:text-red-400'}"
					>
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
