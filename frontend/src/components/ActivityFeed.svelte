<script lang="ts">
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
		return new Date(dateStr).toLocaleString();
	}
</script>

<div class="card">
	<h3>Recent Activity</h3>
	<div style="overflow-x: auto;">
		<table>
			<thead>
				<tr>
					<th>Date</th>
					<th>Subject</th>
					<th>Sender</th>
					<th>Status</th>
					<th>Category</th>
				</tr>
			</thead>
			<tbody>
				{#each activities as item (item.id || item.processed_at)}
					<tr>
						<td style="font-size: 0.85rem; color: var(--text-secondary);"
							>{formatDate(item.processed_at)}</td
						>
						<td style="font-weight: 500;">{item.subject}</td>
						<td>{item.sender}</td>
						<td>
							<span class="badge {item.status}">
								{item.status}
							</span>
						</td>
						<td>
							{#if item.category}
								<span
									style="background: #e5e7eb; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;"
								>
									{item.category}
								</span>
							{/if}
						</td>
					</tr>
				{:else}
					<tr>
						<td
							colspan="5"
							style="text-align: center; color: var(--text-secondary); padding: 2rem;"
						>
							No activity found.
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
