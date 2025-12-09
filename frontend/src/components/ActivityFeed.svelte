<script lang="ts">
	import { FileText, Clock, User, Tag, Activity as ActivityIcon } from 'lucide-svelte';

	interface Activity {
		id: number;
		processed_at: string;
		subject: string;
		sender: string;
		status: string;
		category?: string | null;
	}

	export let activities: Activity[] = [];

	function formatDate(dateStr: string) {
		if (!dateStr) return '';
		return new Date(dateStr).toLocaleString(undefined, {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'forwarded':
				return 'bg-green-100 text-green-700 border-green-200';
			case 'blocked':
			case 'ignored':
				return 'bg-red-100 text-red-700 border-red-200';
			default:
				return 'bg-gray-100 text-gray-700 border-gray-200';
		}
	}
</script>

<div class="card overflow-hidden">
	<div class="flex items-center gap-2 mb-6 pb-4 border-b border-gray-100">
		<div class="p-2 bg-blue-50 text-blue-600 rounded-lg">
			<FileText size={20} />
		</div>
		<h3 class="text-lg font-bold text-text-main m-0">Recent Activity</h3>
	</div>

	<div class="overflow-x-auto">
		<table class="w-full text-left border-collapse">
			<thead>
				<tr class="border-b border-gray-100">
					<th
						class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50 rounded-l-lg"
					>
						<div class="flex items-center gap-1"><Clock size={12} /> Date</div>
					</th>
					<th
						class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50"
					>
						Subject
					</th>
					<th
						class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50"
					>
						<div class="flex items-center gap-1"><User size={12} /> Sender</div>
					</th>
					<th
						class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50"
					>
						<div class="flex items-center gap-1"><ActivityIcon size={12} /> Status</div>
					</th>
					<th
						class="py-3 px-4 text-xs font-semibold text-text-secondary uppercase tracking-wider bg-gray-50/50 rounded-r-lg"
					>
						<div class="flex items-center gap-1"><Tag size={12} /> Category</div>
					</th>
				</tr>
			</thead>
			<tbody class="text-sm">
				{#each activities as item (item.id || item.processed_at)}
					<tr
						class="group hover:bg-gray-50/80 transition-colors border-b border-gray-50 last:border-0"
					>
						<td class="py-4 px-4 text-text-secondary font-medium whitespace-nowrap">
							{formatDate(item.processed_at)}
						</td>
						<td
							class="py-4 px-4 font-medium text-text-main group-hover:text-primary transition-colors max-w-[200px] truncate"
							title={item.subject}
						>
							{item.subject}
						</td>
						<td class="py-4 px-4 text-text-secondary max-w-[150px] truncate" title={item.sender}>
							{item.sender}
						</td>
						<td class="py-4 px-4">
							<span
								class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border {getStatusColor(
									item.status
								)} capitalize"
							>
								{item.status}
							</span>
						</td>
						<td class="py-4 px-4">
							{#if item.category}
								<span
									class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200"
								>
									{item.category}
								</span>
							{/if}
						</td>
					</tr>
				{:else}
					<tr>
						<td colspan="5" class="py-12 text-center text-text-secondary">
							<div class="flex flex-col items-center justify-center gap-2">
								<FileText size={32} class="opacity-20" />
								<p>No activity found yet.</p>
							</div>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
