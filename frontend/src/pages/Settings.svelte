<script lang="ts">
	import PreferenceList from '../components/PreferenceList.svelte';
	import { fetchJson } from '../lib/api';

	async function triggerPoll() {
		try {
			if (!confirm('Run email check now?')) return;
			const res = await fetchJson('/settings/trigger-poll', { method: 'POST' });
			alert(res.message || 'Poll triggered');
		} catch {
			alert('Error triggering poll');
		}
	}
</script>

<h1>Settings</h1>
<p style="color: var(--text-secondary); margin-bottom: 2rem;">
	Manage your detection rules and preferences.
</p>

<div style="margin-bottom: 2rem;">
	<button
		on:click={triggerPoll}
		style="padding: 0.5rem 1rem; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer;"
	>
		Run Now
	</button>
</div>

<PreferenceList type="preferences" />
<PreferenceList type="rules" />
