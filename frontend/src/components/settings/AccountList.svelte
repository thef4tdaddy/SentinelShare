<script lang="ts">
	import { SvelteSet } from 'svelte/reactivity';
	import { fetchJson } from '../../lib/api';
	import { toasts } from '../../lib/stores/toast';
	import {
		Trash2,
		Plus,
		CheckCircle,
		XCircle,
		Loader2,
		Mail,
		Key,
		ShieldCheck
	} from 'lucide-svelte';
	import { onMount } from 'svelte';

	interface EmailAccount {
		id: number;
		email: string;
		host: string;
		port: number;
		username: string;
		is_active: boolean;
		created_at: string;
		updated_at: string;
		auth_method?: string;
		provider?: string;
	}

	interface Props {
		onDeleteRequest?: (id: number, email: string, onComplete: () => void) => void;
	}

	let { onDeleteRequest }: Props = $props();

	let accounts: EmailAccount[] = $state([]);
	let loadingAccounts = $state(false);
	let addingAccount = $state(false);
	let deletingAccountId: number | null = $state(null);
	let showAddForm = $state(false);
	let testingAccounts = new SvelteSet<number>();

	// Form fields
	let formEmail = $state('');
	let formHost = $state('imap.gmail.com');
	let formPort = $state(993);
	let formUsername = $state('');
	let formPassword = $state('');

	async function loadAccounts() {
		try {
			loadingAccounts = true;
			accounts = await fetchJson('/settings/accounts');
		} catch {
			toasts.trigger('Failed to load accounts', 'error');
		} finally {
			loadingAccounts = false;
		}
	}

	function connectWithOAuth(provider: 'google' | 'microsoft') {
		// Redirect to OAuth authorization endpoint
		const baseUrl = window.location.origin;
		const authUrl = `${baseUrl}/api/auth/${provider}/authorize`;
		window.location.href = authUrl;
	}

	async function addAccount() {
		if (!formEmail || !formUsername || !formPassword) {
			toasts.trigger('Please fill all required fields', 'error');
			return;
		}

		try {
			addingAccount = true;
			await fetchJson('/settings/accounts', {
				method: 'POST',
				body: JSON.stringify({
					email: formEmail,
					host: formHost,
					port: formPort,
					username: formUsername,
					password: formPassword
				})
			});

			toasts.trigger('Account added successfully', 'success');

			// Reset form
			formEmail = '';
			formHost = 'imap.gmail.com';
			formPort = 993;
			formUsername = '';
			formPassword = '';
			showAddForm = false;

			// Reload accounts
			await loadAccounts();
		} catch (e) {
			const errorMsg = e instanceof Error ? e.message : 'Failed to add account';
			toasts.trigger(errorMsg, 'error');
		} finally {
			addingAccount = false;
		}
	}

	async function deleteAccount(id: number, email: string) {
		// Use parent callback if provided (for ConfirmDialog)
		if (onDeleteRequest) {
			onDeleteRequest(id, email, loadAccounts);
			return;
		}

		// Fallback to browser confirm if no callback provided
		if (!confirm('Are you sure you want to delete this account?')) return;

		try {
			deletingAccountId = id;
			await fetchJson(`/settings/accounts/${id}`, { method: 'DELETE' });
			toasts.trigger('Account deleted', 'success');
			await loadAccounts();
		} catch {
			toasts.trigger('Failed to delete account', 'error');
		} finally {
			deletingAccountId = null;
		}
	}

	async function testAccount(id: number) {
		try {
			testingAccounts.add(id);
			const result = await fetchJson(`/settings/accounts/${id}/test`, { method: 'POST' });

			if (result.success) {
				toasts.trigger(`Connection to ${result.account} successful`, 'success');
			} else {
				toasts.trigger(`Connection failed: ${result.error}`, 'error');
			}
		} catch {
			toasts.trigger('Failed to test connection', 'error');
		} finally {
			testingAccounts.delete(id);
		}
	}

	onMount(() => {
		loadAccounts();

		// Check for OAuth success/error in URL params
		const params = new URLSearchParams(window.location.search);
		if (params.get('oauth_success') === 'true') {
			const email = params.get('email');
			toasts.trigger(`Successfully connected ${email}!`, 'success');
			// Clean up URL
			window.history.replaceState({}, '', window.location.pathname);
			loadAccounts();
		} else if (params.get('oauth_error') === 'true') {
			const message = params.get('message') || 'OAuth authentication failed';
			toasts.trigger(message, 'error');
			// Clean up URL
			window.history.replaceState({}, '', window.location.pathname);
		}
	});
</script>

<div class="space-y-4">
	<!-- Header with Add Button -->
	<div class="flex items-center justify-between">
		<h4 class="text-md font-semibold text-text-main">Email Accounts</h4>
		<button
			onclick={() => (showAddForm = !showAddForm)}
			class="btn btn-secondary btn-sm"
			disabled={addingAccount}
		>
			<Plus size={16} />
			Add Account
		</button>
	</div>

	<!-- Add Account Form -->
	{#if showAddForm}
		<div class="card p-4 space-y-4 border-l-4 border-l-blue-500">
			<h5 class="font-medium text-text-main">Add New Email Account</h5>

			<!-- OAuth Options -->
			<div class="space-y-3">
				<p class="text-sm text-text-secondary">Connect using OAuth2 (Recommended):</p>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
					<button
						onclick={() => connectWithOAuth('google')}
						class="btn bg-white hover:bg-gray-50 text-gray-800 border border-gray-300 justify-center items-center gap-2"
					>
						<svg class="w-5 h-5" viewBox="0 0 24 24">
							<path
								fill="#4285F4"
								d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
							/>
							<path
								fill="#34A853"
								d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
							/>
							<path
								fill="#FBBC05"
								d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
							/>
							<path
								fill="#EA4335"
								d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
							/>
						</svg>
						Connect with Google
					</button>
					<button
						onclick={() => connectWithOAuth('microsoft')}
						class="btn bg-white hover:bg-gray-50 text-gray-800 border border-gray-300 justify-center items-center gap-2"
						disabled
						title="Coming soon"
					>
						<svg class="w-5 h-5" viewBox="0 0 24 24">
							<path fill="#f25022" d="M0 0h11.5v11.5H0z" />
							<path fill="#00a4ef" d="M12.5 0H24v11.5H12.5z" />
							<path fill="#7fba00" d="M0 12.5h11.5V24H0z" />
							<path fill="#ffb900" d="M12.5 12.5H24V24H12.5z" />
						</svg>
						Connect with Microsoft
						<span class="text-xs opacity-50">(Soon)</span>
					</button>
				</div>
			</div>

			<!-- Divider -->
			<div class="relative">
				<div class="absolute inset-0 flex items-center">
					<div class="w-full border-t border-gray-300"></div>
				</div>
				<div class="relative flex justify-center text-sm">
					<span class="px-2 bg-surface-primary text-text-secondary">Or use manual IMAP setup</span>
				</div>
			</div>

			<!-- Manual IMAP Form -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
				<div>
					<label for="email" class="block text-sm font-medium text-text-secondary mb-1">
						Email Address *
					</label>
					<input
						id="email"
						type="email"
						bind:value={formEmail}
						placeholder="user@example.com"
						class="input w-full"
						required
					/>
				</div>

				<div>
					<label for="username" class="block text-sm font-medium text-text-secondary mb-1">
						Username *
					</label>
					<input
						id="username"
						type="text"
						bind:value={formUsername}
						placeholder="Usually same as email"
						class="input w-full"
						required
					/>
				</div>

				<div>
					<label for="host" class="block text-sm font-medium text-text-secondary mb-1">
						IMAP Host
					</label>
					<input id="host" type="text" bind:value={formHost} class="input w-full" />
				</div>

				<div>
					<label for="port" class="block text-sm font-medium text-text-secondary mb-1">
						IMAP Port
					</label>
					<input id="port" type="number" bind:value={formPort} class="input w-full" />
				</div>

				<div class="md:col-span-2">
					<label for="password" class="block text-sm font-medium text-text-secondary mb-1">
						Password / App Password *
					</label>
					<input
						id="password"
						type="password"
						bind:value={formPassword}
						placeholder="Enter password or app-specific password"
						class="input w-full"
						required
					/>
				</div>
			</div>

			<div class="flex gap-2 justify-end">
				<button
					onclick={() => {
						showAddForm = false;
						formEmail = '';
						formUsername = '';
						formPassword = '';
						formHost = 'imap.gmail.com';
						formPort = 993;
					}}
					class="btn btn-secondary btn-sm"
					disabled={addingAccount}
				>
					Cancel
				</button>
				<button onclick={addAccount} class="btn btn-primary btn-sm" disabled={addingAccount}>
					{#if addingAccount}
						<Loader2 size={16} class="animate-spin" />
					{:else}
						<Plus size={16} />
					{/if}
					Add Account
				</button>
			</div>
		</div>
	{/if}

	<!-- Accounts List -->
	<div class="space-y-2">
		{#if loadingAccounts && accounts.length === 0}
			<div class="text-center py-8 text-text-secondary">
				<Loader2 class="animate-spin mx-auto mb-2" size={24} />
				<p>Loading accounts...</p>
			</div>
		{:else if accounts.length === 0}
			<div class="card p-6 text-center text-text-secondary">
				<Mail class="mx-auto mb-2 opacity-50" size={32} />
				<p>No email accounts configured yet.</p>
				<p class="text-sm mt-1">Add an account to start monitoring for receipts.</p>
			</div>
		{:else}
			{#each accounts as account (account.id)}
				<div class="card p-4 flex items-center justify-between gap-4">
					<div class="flex-1 min-w-0">
						<div class="flex items-center gap-2 flex-wrap">
							<p class="font-medium text-text-main truncate">{account.email}</p>
							{#if account.is_active}
								<CheckCircle class="text-green-500 shrink-0" size={16} />
							{:else}
								<XCircle class="text-gray-400 shrink-0" size={16} />
							{/if}
							{#if account.auth_method === 'oauth2'}
								<span
									class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
									title="OAuth2 Authentication"
								>
									<ShieldCheck size={12} />
									OAuth2
								</span>
							{:else}
								<span
									class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
									title="Password Authentication"
								>
									<Key size={12} />
									Password
								</span>
							{/if}
						</div>
						<p class="text-xs text-text-secondary flex items-center gap-2">
							{account.host}:{account.port}
							{#if account.id < 0}
								<span
									class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
								>
									Defined in Env
								</span>
							{/if}
						</p>
					</div>

					<div class="flex gap-2 shrink-0">
						<button
							onclick={() => testAccount(account.id)}
							class="btn btn-secondary btn-sm"
							disabled={testingAccounts.has(account.id)}
						>
							{#if testingAccounts.has(account.id)}
								<Loader2 size={14} class="animate-spin" />
							{:else}
								<CheckCircle size={14} />
							{/if}
							Test
						</button>
						<button
							onclick={() => deleteAccount(account.id, account.email)}
							class="btn btn-sm bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
							disabled={deletingAccountId === account.id || account.id < 0}
							title={account.id < 0
								? 'Cannot delete environment variable account'
								: 'Delete account'}
						>
							{#if deletingAccountId === account.id}
								<Loader2 size={14} class="animate-spin" />
							{:else}
								<Trash2 size={14} />
							{/if}
						</button>
					</div>
				</div>
			{/each}
		{/if}
	</div>
</div>
