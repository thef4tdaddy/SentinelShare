<script lang="ts">
	import { Mail, CheckCircle, XCircle, AlertCircle } from 'lucide-svelte';
	import type { Stats } from '../lib/types';

	interface HistoryStatsProps {
		stats: Stats;
	}

	let { stats }: HistoryStatsProps = $props();
</script>

<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
	<div class="card">
		<div class="flex items-center justify-between">
			<div>
				<p class="text-text-secondary text-sm mb-1">Total Processed</p>
				<p class="text-2xl font-bold text-text-main dark:text-text-main-dark">{stats.total}</p>
			</div>
			<div class="p-3 bg-blue-50 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400 rounded-lg">
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
			<div
				class="p-3 bg-emerald-50 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-400 rounded-lg"
			>
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
			<div class="p-3 bg-gray-50 text-gray-600 dark:bg-gray-800 dark:text-gray-400 rounded-lg">
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
			<div class="p-3 bg-red-50 text-red-600 dark:bg-red-900/50 dark:text-red-400 rounded-lg">
				<AlertCircle size={24} />
			</div>
		</div>
	</div>
</div>
