<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchJson } from '../lib/api';
	import { Shield, ShieldCheck, ShieldAlert, Check, X, Loader2 } from 'lucide-svelte';

	export let token: string | null = null;
	export let isAdmin = false;

	let email = '';
	let blocked: string[] = [];
	let allowed: string[] = [];
	let loading = true;
	let saving = false;
	let message = '';
	let error = '';

	async function loadPreferences() {
		loading = true;
		error = '';
		try {
			const url = token
				? `/actions/preferences-for-sendee?token=${encodeURIComponent(token)}`
				: '/actions/preferences-for-sendee'; // Admin uses session via same endpoint

			const res = await fetchJson(url);
			if (res.success) {
				email = res.email;
				blocked = res.blocked || [];
				allowed = res.allowed || [];
			} else {
				error = 'Failed to load preferences.';
			}
		} catch (e: unknown) {
			error = (e as Error).message || 'Unauthorized or expired link.';
		} finally {
			loading = false;
		}
	}

	async function saveChanges() {
		saving = true;
		message = '';
		error = '';
		try {
			const res = await fetchJson('/actions/update-preferences', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					token,
					blocked_senders: blocked,
					allowed_senders: allowed
				})
			});
			if (res.success) {
				message = 'Preferences updated successfully!';
				setTimeout(() => (message = ''), 3000);
			}
		} catch (e: unknown) {
			error = (e as Error).message || 'Failed to save changes.';
		} finally {
			saving = false;
		}
	}

	function toggleBlock(item: string) {
		if (blocked.includes(item)) {
			blocked = blocked.filter((i) => i !== item);
		} else {
			blocked = [...blocked, item];
			allowed = allowed.filter((i) => i !== item);
		}
	}

	function toggleAllow(item: string) {
		if (allowed.includes(item)) {
			allowed = allowed.filter((i) => i !== item);
		} else {
			allowed = [...allowed, item];
			blocked = blocked.filter((i) => i !== item);
		}
	}

	onMount(loadPreferences);
</script>

<div class="container-custom max-w-2xl">
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-primary mb-2">Forwarding Preferences</h1>
		<p class="text-text-secondary dark:text-text-secondary-dark">
			{#if isAdmin}
				Manage global forwarding preferences.
			{:else}
				Manage how SentinelShare handles receipts for <strong>{email || 'your account'}</strong>.
			{/if}
		</p>
	</div>

	{#if loading}
		<div class="card flex flex-col items-center justify-center py-12">
			<Loader2 class="animate-spin text-primary mb-4" size={32} />
			<p class="text-text-secondary font-medium">Loading your secure dashboard...</p>
		</div>
	{:else if error}
		<div class="card border-danger/20 bg-danger/5 text-center py-12">
			<ShieldAlert class="text-danger mx-auto mb-4" size={48} />
			<h2 class="text-xl font-bold text-danger mb-2">Access Denied</h2>
			<p class="text-text-secondary mb-6">{error}</p>
			<button class="btn btn-secondary" onclick={() => (window.location.href = '/')}>
				Return Home
			</button>
		</div>
	{:else}
		<div class="space-y-6">
			<!-- Always Forward Section -->
			<div class="card border-emerald-100 bg-linear-to-br from-emerald-50/50 to-white">
				<div class="flex items-center gap-3 mb-4">
					<div class="p-2 bg-emerald-100 text-emerald-600 rounded-lg">
						<ShieldCheck size={20} />
					</div>
					<div>
						<h3 class="font-bold text-emerald-900 m-0">Always Forward</h3>
						<p class="text-xs text-emerald-700/70">
							Receipts from these senders are always allowed.
						</p>
					</div>
				</div>

				{#if allowed.length === 0}
					<p class="text-sm text-center py-4 text-emerald-600/50 italic">
						No senders in your allow-list.
					</p>
				{:else}
					<div class="flex flex-wrap gap-2">
						{#each allowed as item (item)}
							<div
								class="badge bg-emerald-100 text-emerald-700 border border-emerald-200 pl-3 pr-1 py-1 flex items-center gap-2"
							>
								{item}
								<button
									onclick={() => toggleAllow(item)}
									class="hover:bg-emerald-200 rounded-full p-0.5 transition-colors"
								>
									<X size={14} />
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Blocked Section -->
			<div class="card border-danger-100 bg-linear-to-br from-red-50/50 to-white">
				<div class="flex items-center gap-3 mb-4">
					<div class="p-2 bg-danger/10 text-danger rounded-lg">
						<Shield size={20} />
					</div>
					<div>
						<h3 class="font-bold text-danger-900 m-0">Blocked Senders</h3>
						<p class="text-xs text-danger-700/70">
							SentinelShare will ignore all emails from these senders.
						</p>
					</div>
				</div>

				{#if blocked.length === 0}
					<p class="text-sm text-center py-4 text-danger/40 italic">No blocked senders yet.</p>
				{:else}
					<div class="flex flex-wrap gap-2">
						{#each blocked as item (item)}
							<div
								class="badge bg-danger/10 text-danger border border-danger/10 pl-3 pr-1 py-1 flex items-center gap-2"
							>
								{item}
								<button
									onclick={() => toggleBlock(item)}
									class="hover:bg-danger/20 rounded-full p-0.5 transition-colors"
								>
									<X size={14} />
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Success/Error Feedback -->
			{#if message}
				<div
					class="p-3 bg-emerald-500 text-white rounded-lg text-sm font-medium flex items-center gap-2 animate-in fade-in slide-in-from-top-2"
				>
					<Check size={16} />
					{message}
				</div>
			{/if}

			<div class="flex justify-end pt-4">
				<button
					class="btn btn-primary px-8 py-3 shadow-lg hover:shadow-xl active:scale-95 transition-all flex items-center gap-2"
					onclick={saveChanges}
					disabled={saving}
				>
					{#if saving}
						<Loader2 class="animate-spin" size={18} /> Saving...
					{:else}
						Save Preferences
					{/if}
				</button>
			</div>
		</div>
	{/if}
</div>
