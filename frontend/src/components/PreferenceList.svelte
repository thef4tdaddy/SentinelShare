<script lang="ts">
	import { fetchJson } from '../lib/api';
	import { onMount } from 'svelte';

	interface Item {
		id?: number;
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		[key: string]: any; // Allow dynamic access for this form
	}

	export let type: 'preferences' | 'rules';
	let items: Item[] = [];
	let newItem: Item = {};

	// Basic form fields based on type
	let fields =
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
				];

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
			const res = await fetchJson(`/settings/${type}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(newItem)
			});
			items = [...items, res];
			newItem = {}; // Reset
		} catch {
			alert('Error adding item');
		}
	}

	async function deleteItem(id: number) {
		if (!confirm('Are you sure?')) return;
		try {
			await fetchJson(`/settings/${type}/${id}`, { method: 'DELETE' });
			items = items.filter((i) => i.id !== id);
		} catch {
			alert('Error deleting item');
		}
	}
</script>

<div class="card">
	<h3>{type === 'preferences' ? 'Preferences' : 'Manual Rules'}</h3>

	<!-- Add Form -->
	<div style="display: flex; gap: 0.5rem; margin-bottom: 1rem; align-items: flex-end;">
		{#each fields as field (field.key)}
			<div style="flex: 1;">
				<label
					for="{type}-{field.key}"
					style="font-size: 0.8rem; display: block; margin-bottom: 0.25rem;">{field.label}</label
				>
				{#if field.type === 'select'}
					<select id="{type}-{field.key}" bind:value={newItem[field.key]}>
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
					/>
				{/if}
			</div>
		{/each}
		<button on:click={addItem}>Add</button>
	</div>

	<!-- List -->
	<table>
		<thead>
			<tr>
				{#each fields as field (field.key)}
					<th>{field.label}</th>
				{/each}
				<th>Actions</th>
			</tr>
		</thead>
		<tbody>
			{#each items as item (item.id || Math.random())}
				<tr>
					{#each fields as field (field.key)}
						<td>{item[field.key] || '-'}</td>
					{/each}
					<td>
						<button class="secondary danger" on:click={() => item.id && deleteItem(item.id)}
							>Delete</button
						>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
