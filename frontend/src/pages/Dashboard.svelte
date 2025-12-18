<script lang="ts">
	import StatsCard from '../components/StatsCard.svelte';
	import ActivityFeed from '../components/ActivityFeed.svelte';
	import { fetchJson } from '../lib/api';
	import { onMount } from 'svelte';
	import { Mail, Share2, Ban } from 'lucide-svelte';

	interface Activity {
		id: number;
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
			const [statsRes, activityRes] = await Promise.all([
				fetchJson('/dashboard/stats'),
				fetchJson('/dashboard/activity')
			]);

			stats = statsRes;
			activity = activityRes;
		} catch (e) {
			console.error('Failed to load dashboard data', e);
		}
	});
</script>

<div class="mb-8">
	<h2 class="text-2xl font-bold text-text-main mb-1">Dashboard</h2>
	<p class="text-text-secondary text-sm">Overview of your receipt forwarding activity.</p>
</div>

<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
	<StatsCard title="Total Processed" value={stats.total_processed} icon={Mail} variant="default" />
	<StatsCard
		title="Forwarded"
		value={stats.total_forwarded}
		subtext="Receipts found"
		icon={Share2}
		variant="success"
	/>
	<StatsCard
		title="Blocked/Ignored"
		value={stats.total_blocked}
		subtext="Not receipts"
		icon={Ban}
		variant="danger"
	/>
</div>

<ActivityFeed activities={activity} />
