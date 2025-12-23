<script lang="ts">
	import { fetchJson } from '../lib/api';
	import { onMount } from 'svelte';
	import { Zap, Eye, Trash2, TrendingUp, ShieldCheck } from 'lucide-svelte';
	import SuggestedRules from '../components/SuggestedRules.svelte';

	interface Rule {
		id: number;
		email_pattern?: string;
		subject_pattern?: string;
		priority: number;
		purpose?: string;
		confidence: number;
		is_shadow_mode: boolean;
		match_count: number;
	}

	let rules: Rule[] = [];
	let loading = true;

	async function loadRules() {
		loading = true;
		try {
			// Reuse settings endpoint but we will enhance it if needed
			const res = await fetchJson('/api/settings/manual-rules');
			rules = res;
		} catch (e) {
			console.error('Failed to load rules', e);
		} finally {
			loading = false;
		}
	}

	async function deleteRule(id: number) {
		if (!confirm('Are you sure you want to delete this rule?')) return;
		try {
			await fetchJson(`/api/settings/manual-rule/${id}`, { method: 'DELETE' });
			await loadRules();
		} catch (e) {
			console.error('Failed to delete rule', e);
		}
	}

	onMount(loadRules);
</script>

<div class="mb-8">
	<h2 class="text-2xl font-bold text-text-main mb-1">
		Automation Rules {#if loading}(Loading...){/if}
	</h2>
	<p class="text-text-secondary text-sm">
		Manage automated detection rules, adaptive learning, and shadow mode candidates.
	</p>
</div>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
	<div class="card bg-linear-to-br from-indigo-50 to-white border-indigo-100">
		<div class="flex items-center gap-3 mb-4">
			<div class="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
				<Zap size={20} />
			</div>
			<h3 class="font-bold text-indigo-900 m-0">Adaptive Learning</h3>
		</div>
		<p class="text-sm text-indigo-800 mb-4">
			System is currently monitoring feedback and suggesting new rules in Shadow Mode.
		</p>
		<div class="flex items-center gap-2 text-xs font-semibold text-indigo-600">
			<ShieldCheck size={14} />
			SHADOW MODE ACTIVE
		</div>
	</div>

	<div class="card bg-linear-to-br from-emerald-50 to-white border-emerald-100">
		<div class="flex items-center gap-3 mb-4">
			<div class="p-2 bg-emerald-100 text-emerald-600 rounded-lg">
				<TrendingUp size={20} />
			</div>
			<h3 class="font-bold text-emerald-900 m-0">Auto-Apply</h3>
		</div>
		<p class="text-sm text-emerald-800 mb-4">
			Rules with >90% confidence and 3+ successful shadow matches are auto-promoted.
		</p>
		<div class="text-xs font-semibold text-emerald-600 uppercase">Confidence Threshold: 90%</div>
	</div>

	<div class="card">
		<div class="flex items-center gap-3 mb-4">
			<div class="p-2 bg-gray-100 text-gray-600 rounded-lg">
				<Eye size={20} />
			</div>
			<h3 class="font-bold text-text-main m-0">Shadow Stats</h3>
		</div>
		<div class="space-y-2">
			<div class="flex justify-between text-sm">
				<span class="text-text-secondary">Candidates:</span>
				<span class="font-mono font-bold">{rules.filter((r) => r.is_shadow_mode).length}</span>
			</div>
			<div class="flex justify-between text-sm">
				<span class="text-text-secondary">Auto-Applied:</span>
				<span class="font-mono font-bold text-emerald-600"
					>{rules.filter((r) => !r.is_shadow_mode && r.purpose?.includes('(AUTO)')).length}</span
				>
			</div>
		</div>
	</div>
</div>

<!-- Suggested Rules Component -->
<SuggestedRules onRuleAdded={loadRules} />

<div class="card">
	<div class="flex items-center justify-between mb-6">
		<h3 class="text-lg font-bold text-text-main m-0">Active & Suggested Rules</h3>
		<div class="flex gap-2">
			<span class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">Manual</span>
			<span class="px-2 py-1 bg-indigo-100 text-indigo-600 rounded text-xs">Shadow</span>
			<span class="px-2 py-1 bg-emerald-100 text-emerald-600 rounded text-xs">Auto</span>
		</div>
	</div>

	<div class="overflow-x-auto">
		<table class="w-full text-left">
			<thead>
				<tr class="border-b border-gray-100 text-xs font-semibold text-text-secondary uppercase">
					<th class="py-3 px-4">Type</th>
					<th class="py-3 px-4">Pattern</th>
					<th class="py-3 px-4">Confidence</th>
					<th class="py-3 px-4">Matches</th>
					<th class="py-3 px-4">Actions</th>
				</tr>
			</thead>
			<tbody class="divide-y divide-gray-50">
				{#each rules as rule (rule.id)}
					<tr class="hover:bg-gray-50/50 transition-colors">
						<td class="py-3 px-4">
							{#if rule.is_shadow_mode}
								<span
									class="px-2 py-0.5 rounded-full text-[10px] font-bold border bg-indigo-50 text-indigo-700 border-indigo-100"
									>SHADOW</span
								>
							{:else if rule.purpose?.includes('(AUTO)')}
								<span
									class="px-2 py-0.5 rounded-full text-[10px] font-bold border bg-emerald-50 text-emerald-700 border-emerald-100"
									>AUTO</span
								>
							{:else}
								<span
									class="px-2 py-0.5 rounded-full text-[10px] font-bold border bg-gray-50 text-gray-700 border-gray-100"
									>MANUAL</span
								>
							{/if}
						</td>
						<td class="py-3 px-4">
							<div class="text-sm font-medium text-text-main">
								{rule.email_pattern || 'Any Sender'}
							</div>
							{#if rule.subject_pattern}
								<div class="text-xs text-text-secondary">Subject: {rule.subject_pattern}</div>
							{/if}
							<div class="text-[10px] text-gray-400 mt-1 italic">
								{rule.purpose || 'No description'}
							</div>
						</td>
						<td class="py-3 px-4">
							<div class="flex items-center gap-2">
								<div class="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden min-w-[60px]">
									<div
										class="h-full {rule.confidence > 0.8 ? 'bg-emerald-500' : 'bg-indigo-500'}"
										style="width: {rule.confidence * 100}%"
									></div>
								</div>
								<span class="text-xs font-mono font-bold"
									>{(rule.confidence * 100).toFixed(0)}%</span
								>
							</div>
						</td>
						<td class="py-3 px-4 text-sm font-mono">{rule.match_count}</td>
						<td class="py-3 px-4 text-right">
							<button
								onclick={() => deleteRule(rule.id)}
								class="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
								title="Delete Rule"
							>
								<Trash2 size={16} />
							</button>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
