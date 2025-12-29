<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { Lock, LogIn } from 'lucide-svelte';

	export let onLoginSuccess: () => void;

	let passwordField: HTMLInputElement;
	let password = '';
	let error = '';
	let loading = false;

	onMount(async () => {
		await tick();
		passwordField?.focus();
	});

	async function handleLogin(e?: Event) {
		e?.preventDefault();
		loading = true;
		error = '';

		try {
			const res = await fetch('/api/auth/login', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ password })
			});

			if (res.ok) {
				const data = await res.json();
				if (data.status === 'success') {
					onLoginSuccess();
				}
			} else {
				error = 'Invalid password';
			}
		} catch {
			error = 'Connection error';
		} finally {
			loading = false;
		}
	}
</script>

<div class="h-screen w-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
	<div class="w-full max-w-md bg-white p-8 rounded-xl shadow-lg border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
		<div class="flex flex-col items-center mb-8">
			<div class="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mb-4 dark:bg-blue-900/50">
				<Lock class="w-8 h-8 text-primary dark:text-primary-dark" />
			</div>
			<h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">SentinelShare</h1>
			<p class="text-gray-500 text-sm mt-1 dark:text-gray-400">Single-User Access</p>
		</div>

		<form onsubmit={handleLogin} class="space-y-4">
			<div>
				<label for="password" class="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Password</label>
				<input
					type="password"
					id="password"
					bind:this={passwordField}
					bind:value={password}
					class="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:focus:ring-primary-dark"
					placeholder="Enter dashboard password..."
				/>
			</div>

			{#if error}
				<div class="text-red-500 text-sm text-center bg-red-50 p-2 rounded dark:bg-red-900/30 dark:text-red-300">
					{error}
				</div>
			{/if}

			<button
				type="submit"
				disabled={loading}
				class="w-full btn btn-primary flex justify-center items-center gap-2 py-2.5"
			>
				{#if loading}
					<span class="loading loading-spinner loading-xs"></span>
				{:else}
					<LogIn size={18} />
				{/if}
				{loading ? 'Verifying...' : 'Access Dashboard'}
			</button>
		</form>
	</div>
</div>
