<script lang="ts">
	import { Clock, CheckCircle, XCircle, AlertCircle, History as HistoryIcon } from 'lucide-svelte';
	import { formatDate } from '../lib/dateUtils';

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

	interface ProcessingRunsListProps {
		runs: Run[];
	}

	let { runs }: ProcessingRunsListProps = $props();
</script>

<div class="card">
	<div class="flex items-center gap-2 mb-6 pb-4 border-b border-gray-100 dark:border-gray-700">
		<div
			class="p-2 bg-purple-50 text-purple-600 dark:bg-purple-900/50 dark:text-purple-400 rounded-lg"
		>
			<HistoryIcon size={20} />
		</div>
		<h3 class="text-lg font-bold text-text-main m-0">Recent Processing Runs</h3>
	</div>

	<div class="space-y-4">
		{#if runs.length === 0}
			<div class="py-12 text-center text-text-secondary dark:text-text-secondary-dark">
				<div class="flex flex-col items-center justify-center gap-3">
					<div class="bg-gray-100 dark:bg-gray-800 p-3 rounded-full">
						<HistoryIcon size={24} class="text-gray-400 dark:text-gray-500" />
					</div>
					<p>No processing runs found.</p>
				</div>
			</div>
		{:else}
			{#each runs ?? [] as run (run.run_time)}
				<div
					class="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-primary transition-colors"
				>
					<div class="flex items-center justify-between mb-3">
						<div class="flex items-center gap-2">
							<Clock size={16} class="text-primary" />
							<span class="font-semibold text-text-main dark:text-text-main-dark">
								{formatDate(run.run_time)}
							</span>
						</div>
						<div class="text-sm text-text-secondary dark:text-text-secondary-dark">
							{run.total_emails} email{run.total_emails !== 1 ? 's' : ''}
						</div>
					</div>

					<div class="grid grid-cols-3 gap-4">
						<div class="flex items-center gap-2">
							<CheckCircle size={16} class="text-emerald-600" />
							<div>
								<div class="text-sm text-text-secondary dark:text-text-secondary-dark">
									Forwarded
								</div>
								<div class="font-semibold text-emerald-600">{run.forwarded}</div>
							</div>
						</div>
						<div class="flex items-center gap-2">
							<XCircle size={16} class="text-gray-600" />
							<div>
								<div class="text-sm text-text-secondary dark:text-text-secondary-dark">Blocked</div>
								<div class="font-semibold text-gray-600">{run.blocked}</div>
							</div>
						</div>
						<div class="flex items-center gap-2">
							<AlertCircle size={16} class="text-red-600" />
							<div>
								<div class="text-sm text-text-secondary dark:text-text-secondary-dark">Errors</div>
								<div class="font-semibold text-red-600">{run.errors}</div>
							</div>
						</div>
					</div>
				</div>
			{/each}
		{/if}
	</div>
</div>
