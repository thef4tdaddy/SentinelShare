<script lang="ts">
	import { fetchJson } from '../lib/api';
	import { onMount } from 'svelte';
	import { Trash2, Plus } from 'lucide-svelte';
	import ConfirmDialog from './ConfirmDialog.svelte';

	interface Item {
		id?: number;
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		[key: string]: any;
	}

	interface PreferenceListProps {
		type: 'preferences' | 'rules';
	}

	let { type }: PreferenceListProps = $props();
	let items: Item[] = $state([]);
	let newItem: Item = $state({});
	let loading = $state(false);
	let showDeleteConfirm = $state(false);
	let itemToDelete: number | null = $state(null);

	// Basic form fields based on type
	let fields = $derived(
		type === 'preferences'
			? [
					{ key: 'item', label: 'Item (e.g., amazon)' },
					{
						key: 'type',
						label: 'Type',
						type: 'select',
						options: ['Blocked Sender', 'Always Forward', 'Blocked Category']
					}
				]
			: [
					{ key: 'email_pattern', label: 'Email Pattern' },
					{ key: 'subject_pattern', label: 'Subject Pattern' },
					{ key: 'purpose', label: 'Purpose' }
				]
	);

	onMount(loadItems);

	async function loadItems() {
		try {
			items = await fetchJson(`/settings/${type}`);
		} catch {
			console.error('Error loading items');
		}
	}

	async function addItem() {
		try {
			loading = true;
			const res = await fetchJson(`/settings/${type}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(newItem)
			});
			items = [...items, res];
			newItem = {}; // Reset
		} catch {
			alert('Error adding item');
		} finally {
			loading = false;
		}
	}

	async function deleteItem(id: number) {
		itemToDelete = id;
		showDeleteConfirm = true;
	}

	async function handleConfirmDelete() {
		if (itemToDelete === null) return;
		showDeleteConfirm = false;
		try {
			await fetchJson(`/settings/${type}/${itemToDelete}`, { method: 'DELETE' });
			items = items.filter((i) => i.id !== itemToDelete);
		} catch {
			alert('Error deleting item');
		} finally {
			itemToDelete = null;
		}
	}

	function handleCancelDelete() {
		showDeleteConfirm = false;
		itemToDelete = null;
	}
</script>

<div class="card overflow-hidden">
	<!-- Add Form -->
	<div class="p-4 bg-gray-50 border-b border-gray-100 mb-4 rounded-lg">
		<h4 class="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-3">
			Add New {type === 'preferences' ? 'Preference' : 'Rule'}
		</h4>
		<div class="flex flex-col md:flex-row gap-3 items-end">
			{#each fields as field (field.key)}
				<div class="w-full">
					<label
						for="{type}-{field.key}"
						class="block text-xs font-medium text-text-secondary mb-1.5 ml-1">{field.label}</label
					>
					{#if field.type === 'select'}
						<select id="{type}-{field.key}" bind:value={newItem[field.key]} class="input-field">
							<option value="" disabled selected>Select type...</option>
							{#each field.options as opt (opt)}
								<option value={opt}>{opt}</option>
							{/each}
						</select>
					{:else}
						<input
							id="{type}-{field.key}"
							type="text"
							bind:value={newItem[field.key]}
							placeholder={field.label}
							class="input-field"
						/>
					{/if}
				</div>
			{/each}
			<button on:click={addItem} disabled={loading} class="btn btn-accent h-[42px] px-6">
				{#if loading}
					...
				{:else}
					<Plus size={18} /> Add
				{/if}
			</button>
		</div>
	</div>

	<!-- List -->
	<div class="overflow-x-auto">
		<table class="w-full text-left text-sm">
			<thead>
				<tr class="border-b border-gray-100">
					{#each fields as field (field.key)}
						<th
							class="py-3 px-4 font-semibold text-text-secondary bg-gray-50/50 first:rounded-tl-lg"
							>{field.label}</th
						>
					{/each}
					<th
						class="py-3 px-4 font-semibold text-text-secondary bg-gray-50/50 w-20 text-right rounded-tr-lg"
						>Action</th
					>
				</tr>
			</thead>
			<tbody>
				{#each items as item (item.id || Math.random())}
					<tr
						class="border-b border-gray-50 last:border-0 hover:bg-gray-50/80 transition-colors group"
					>
						{#each fields as field (field.key)}
							<td class="py-3 px-4 text-text-main font-medium">{item[field.key] || '-'}</td>
						{/each}
						<td class="py-3 px-4 text-right">
							<button
								class="p-2 text-text-secondary hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
								on:click={() => item.id && deleteItem(item.id)}
								title="Delete"
							>
								<Trash2 size={16} />
							</button>
						</td>
					</tr>
				{:else}
					<tr>
						<td colspan={fields.length + 1} class="py-8 text-center text-text-secondary text-sm">
							No items found.
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>

<ConfirmDialog
	bind:isOpen={showDeleteConfirm}
	onConfirm={handleConfirmDelete}
	onCancel={handleCancelDelete}
	title="Confirm Delete"
	message="Are you sure you want to delete this {type === 'preferences'
		? 'preference'
		: 'rule'}? This action cannot be undone."
	confirmText="Delete"
	cancelText="Cancel"
	danger={true}
/>
