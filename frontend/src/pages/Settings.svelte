<script lang="ts">
	import PreferenceList from '../components/PreferenceList.svelte';
	import EmailTemplateEditor from '../components/EmailTemplateEditor.svelte';
	import { fetchJson } from '../lib/api';
	import { Play, Settings, Sliders, Mail } from 'lucide-svelte';

	let loading = false;

	async function triggerPoll() {
		try {
			loading = true;
			if (!confirm('Run email check now?')) {
				loading = false;
				return;
			}
			const res = await fetchJson('/settings/trigger-poll', { method: 'POST' });
			alert(res.message || 'Poll triggered');
		} catch {
			alert('Error triggering poll');
		} finally {
			loading = false;
		}
	}
</script>

<div class="mb-8 flex items-center justify-between">
	<div>
		<h2 class="text-2xl font-bold text-text-main mb-1">Settings</h2>
		<p class="text-text-secondary text-sm">Manage detection rules and preferences.</p>
	</div>

	<button on:click={triggerPoll} disabled={loading} class="btn btn-primary">
		<Play size={16} class={loading ? 'animate-spin' : ''} />
		{loading ? 'Running...' : 'Run Now'}
	</button>
</div>

<div class="space-y-8">
	<!-- Email Template Section -->
	<section>
		<div class="flex items-center gap-2 mb-4">
			<Mail size={20} class="text-text-secondary" />
			<h3 class="text-lg font-bold text-text-main">Email Template</h3>
		</div>
		<EmailTemplateEditor />
	</section>

	<!-- Preferences Section -->
	<section>
		<div class="flex items-center gap-2 mb-4">
			<Sliders size={20} class="text-text-secondary" />
			<h3 class="text-lg font-bold text-text-main">Detection Preferences</h3>
		</div>
		<PreferenceList type="preferences" />
	</section>

	<!-- Rules Section -->
	<section>
		<div class="flex items-center gap-2 mb-4">
			<Settings size={20} class="text-text-secondary" />
			<h3 class="text-lg font-bold text-text-main">Manual Rules</h3>
		</div>
		<PreferenceList type="rules" />
	</section>
</div>
