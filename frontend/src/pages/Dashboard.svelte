<script lang="ts">
	import StatsCard from '../components/StatsCard.svelte';
	import ActivityFeed from '../components/ActivityFeed.svelte';
	import { fetchJson } from '../lib/api';
	import { onMount } from 'svelte';

	interface Activity {
		processed_at: string;
		subject: string;
		sender: string;
		status: string;
		category?: string;
	}

	let stats = { total_forwarded: 0, total_blocked: 0, total_processed: 0 };
	let activity: Activity[] = [];

	onMount(async () => {
		try {
			const statsRes = await fetchJson('/dashboard/stats');
			stats = statsRes;

			const activityRes = await fetchJson('/dashboard/activity');
			activity = activityRes;
		} catch (e) {
			console.error('Failed to load dashboard data', e);
		}
	});
</script>

<div
	style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;"
>
	<StatsCard title="Total Processed" value={stats.total_processed} />
	<StatsCard title="Forwarded" value={stats.total_forwarded} subtext="Receipts found" />
	<StatsCard title="Blocked/Ignored" value={stats.total_blocked} subtext="Not receipts" />
</div>

<ActivityFeed activities={activity} />
