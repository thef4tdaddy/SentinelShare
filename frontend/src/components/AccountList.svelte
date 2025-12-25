<script lang="ts">
	import { fetchJson } from '../lib/api';
	import { toasts } from '../lib/stores/toast';
	import { Trash2, Plus, CheckCircle, XCircle, Loader2, Mail } from 'lucide-svelte';
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
	let testingAccounts: Set<number> = $state(new Set());

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
		} catch (e) {
			console.error('Failed to load accounts', e);
			toasts.trigger('Failed to load accounts', 'error');
		} finally {
			loadingAccounts = false;
		}
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
		} catch (e: any) {
			const errorMsg = e?.message || 'Failed to add account';
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
		} catch (e) {
			toasts.trigger('Failed to delete account', 'error');
		} finally {
			deletingAccountId = null;
		}
	}

	async function testAccount(id: number) {
		try {
			testingAccounts = new Set(testingAccounts).add(id);
			const result = await fetchJson(`/settings/accounts/${id}/test`, { method: 'POST' });

			if (result.success) {
				toasts.trigger(`Connection to ${result.account} successful`, 'success');
			} else {
				toasts.trigger(`Connection failed: ${result.error}`, 'error');
			}
		} catch (e) {
			toasts.trigger('Failed to test connection', 'error');
		} finally {
			const newSet = new Set(testingAccounts);
			newSet.delete(id);
			testingAccounts = newSet;
		}
	}

	onMount(() => {
		loadAccounts();
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
		<div class="card p-4 space-y-3 border-l-4 border-l-blue-500">
			<h5 class="font-medium text-text-main">Add New Email Account</h5>

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
						<div class="flex items-center gap-2">
							<p class="font-medium text-text-main truncate">{account.email}</p>
							{#if account.is_active}
								<CheckCircle class="text-green-500 flex-shrink-0" size={16} />
							{:else}
								<XCircle class="text-gray-400 flex-shrink-0" size={16} />
							{/if}
						</div>
						<p class="text-xs text-text-secondary">
							{account.host}:{account.port}
						</p>
					</div>

					<div class="flex gap-2 flex-shrink-0">
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
							class="btn btn-sm bg-red-600 hover:bg-red-700 text-white"
							disabled={deletingAccountId === account.id}
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
