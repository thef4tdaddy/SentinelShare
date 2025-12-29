<script lang="ts">
	import { FileText, Clock, User, Tag, Activity as ActivityIcon, Ban } from 'lucide-svelte';
	import { formatTime, formatShortDate } from '../lib/dateUtils';

	interface Activity {
		id: number;
		processed_at: string;
		subject: string;
		sender: string;
		status: string;
		category?: string | null;
		account_email?: string;
	}

	export let activities: Activity[] = [];
</script>

<div class="card overflow-hidden">
	<div class="flex items-center gap-2 mb-6 pb-4 border-b border-gray-100 dark:border-gray-700">
		<div class="p-2 bg-blue-50 text-blue-600 rounded-lg dark:bg-blue-900/50 dark:text-blue-400">
			<FileText size={20} />
		</div>
		<h3 class="text-lg font-bold text-text-main m-0 dark:text-text-main-dark">Recent Activity</h3>
	</div>

	<div class="overflow-x-auto">
		<table class="w-full text-left border-collapse">
			<thead>
				<tr class="border-b border-gray-100 dark:border-gray-700">
					<th
						class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50 rounded-l-lg dark:text-text-secondary-dark dark:bg-gray-800/50"
					>
						<div class="flex items-center gap-1"><Clock size={12} /> Date</div>
					</th>
					<th class="py-3 px-4 font-semibold text-text-secondary bg-gray-50/50 first:rounded-tl-lg dark:text-text-secondary-dark dark:bg-gray-800/50"
						>Status</th
					>
					<th class="py-3 px-4 font-semibold text-text-secondary bg-gray-50/50 dark:text-text-secondary-dark dark:bg-gray-800/50">Subject</th>
					<th class="py-3 px-4 font-semibold text-text-secondary bg-gray-50/50 dark:text-text-secondary-dark dark:bg-gray-800/50">Account</th>
					<th class="py-3 px-4 font-semibold text-text-secondary bg-gray-50/50 dark:text-text-secondary-dark dark:bg-gray-800/50">Category</th>
					<th
						class="py-3 px-4 font-semibold text-text-secondary bg-gray-50/50 w-32 text-right rounded-tr-lg dark:text-text-secondary-dark dark:bg-gray-800/50"
						>Time</th
					>
				</tr>
			</thead>
			<tbody>
				{#each activities as item (item.id)}
					<tr
						class="border-b border-gray-50 last:border-0 hover:bg-gray-50/80 transition-colors group dark:border-gray-800 dark:hover:bg-gray-800/50"
					>
						<td class="py-3 px-4 text-text-secondary whitespace-nowrap dark:text-text-secondary-dark">
							<div class="flex items-center gap-1.5">
								<span class="text-sm font-medium">
									{formatShortDate(item.processed_at)}
								</span>
							</div>
						</td>
						<td class="py-3 px-4">
							<span
								class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize shadow-sm
                        {item.status === 'forwarded'
									? 'bg-emerald-100 text-emerald-800 border border-emerald-200 dark:bg-emerald-900/50 dark:text-emerald-300 dark:border-emerald-800'
									: item.status === 'blocked' || item.status === 'ignored'
										? 'bg-gray-100 text-gray-600 border border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700'
										: 'bg-red-100 text-red-800 border border-red-200 dark:bg-red-900/50 dark:text-red-300 dark:border-red-800'}"
							>
								{#if item.status === 'forwarded'}
									<ActivityIcon size={12} class="mr-1" />
								{:else}
									<Ban size={12} class="mr-1" />
								{/if}
								{item.status}
							</span>
						</td>
						<td class="py-3 px-4 font-medium text-text-main dark:text-text-main-dark">
							<div class="flex items-center gap-2">
								<span class="truncate max-w-[200px]" title={item.subject}>{item.subject}</span>
							</div>
						</td>
						<td class="py-3 px-4 text-text-secondary dark:text-text-secondary-dark">
							{#if item.account_email}
								<div class="flex items-center gap-1 text-xs">
									<User size={12} />
									{item.account_email}
								</div>
							{:else}
								<span class="text-gray-300 dark:text-gray-600">-</span>
							{/if}
						</td>
						<td class="py-3 px-4 text-text-secondary dark:text-text-secondary-dark">
							<div class="flex items-center gap-1.5">
								<Tag size={13} class="text-gray-400 dark:text-gray-500" />
								{item.category || 'Uncategorized'}
							</div>
						</td>
						<td class="py-3 px-4 text-right text-text-secondary w-32 whitespace-nowrap dark:text-text-secondary-dark">
							<div class="flex items-center justify-end gap-1.5">
								<Clock size={13} class="text-gray-400 dark:text-gray-500" />
								{formatTime(item.processed_at)}
							</div>
						</td>
					</tr>
				{:else}
					<tr>
						<td colspan="6" class="py-12 text-center text-text-secondary dark:text-text-secondary-dark">
							<div class="flex flex-col items-center justify-center gap-3">
								<div class="bg-gray-100 p-3 rounded-full dark:bg-gray-800">
									<FileText size={24} class="text-gray-400 dark:text-gray-500" />
								</div>
								<p>No activity found.</p>
							</div>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
