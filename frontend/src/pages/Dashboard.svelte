<script lang="ts">
	import StatsCard from '../components/StatsCard.svelte';
	import ActivityFeed from '../components/ActivityFeed.svelte';
	import Dropzone from '../components/Dropzone.svelte';
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
	let isUploading = $state(false);
	let uploadMessage = $state<{ type: 'success' | 'error'; text: string } | null>(null);

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

	async function handleFileSelected(file: File) {
		isUploading = true;
		uploadMessage = null;

		try {
			const formData = new FormData();
			formData.append('file', file);

			const response = await fetch('/api/actions/upload', {
				method: 'POST',
				body: formData
			});

			if (!response.ok) {
				const error = await response.json();
				throw new Error(error.detail || 'Upload failed');
			}

			const result = await response.json();
			uploadMessage = {
				type: 'success',
				text: result.message || 'Receipt uploaded successfully!'
			};

			// Refresh activity feed
			const activityRes = await fetchJson('/dashboard/activity');
			activity = activityRes;

			// Refresh stats
			const statsRes = await fetchJson('/dashboard/stats');
			stats = statsRes;
		} catch (e) {
			uploadMessage = {
				type: 'error',
				text: e instanceof Error ? e.message : 'Failed to upload receipt'
			};
		} finally {
			isUploading = false;
		}
	}
</script>

<div class="mb-8">
	<h2 class="text-2xl font-bold text-text-main mb-1 dark:text-text-main-dark">Dashboard</h2>
	<p class="text-text-secondary text-sm dark:text-text-secondary-dark">
		Overview of your receipt forwarding activity.
	</p>
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

<!-- Manual Receipt Upload Section -->
<div class="mb-8">
	<div class="bg-bg-card dark:bg-bg-card-dark rounded-lg border border-border dark:border-border-dark p-6">
		<h3 class="text-lg font-semibold text-text-main dark:text-text-main-dark mb-4">
			Upload Receipt
		</h3>
		<p class="text-sm text-text-secondary dark:text-text-secondary-dark mb-4">
			Manually upload paper receipts or downloaded files.
		</p>
		
		<Dropzone onFileSelected={handleFileSelected} disabled={isUploading} />
		
		{#if uploadMessage}
			<div
				class="mt-4 p-3 rounded-lg {uploadMessage.type === 'success'
					? 'bg-green-50 text-green-800 dark:bg-green-900/20 dark:text-green-400'
					: 'bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-400'}"
			>
				{uploadMessage.text}
			</div>
		{/if}
		
		{#if isUploading}
			<div class="mt-4 flex items-center gap-2 text-text-secondary dark:text-text-secondary-dark">
				<div class="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
				<span class="text-sm">Uploading...</span>
			</div>
		{/if}
	</div>
</div>

<ActivityFeed activities={activity} />
