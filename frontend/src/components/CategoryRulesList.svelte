<script lang="ts">
	import { fetchJson } from '../lib/api';
	import { onMount } from 'svelte';
	import { toasts } from '../lib/stores/toast';
	import { Trash2, Plus, Edit2 } from 'lucide-svelte';
	import ConfirmDialog from './ConfirmDialog.svelte';

	interface CategoryRule {
		id?: number;
		match_type: string;
		pattern: string;
		assigned_category: string;
		priority: number;
		created_at?: string;
	}

	let rules: CategoryRule[] = $state([]);
	let newRule: CategoryRule = $state({
		match_type: 'sender',
		pattern: '',
		assigned_category: '',
		priority: 10
	});
	let editingRule: CategoryRule | null = $state(null);
	let loading = $state(false);
	let showDeleteConfirm = $state(false);
	let ruleToDelete: number | null = $state(null);

	onMount(loadRules);

	async function loadRules() {
		try {
			rules = await fetchJson('/settings/category-rules');
		} catch {
			console.error('Error loading category rules');
		}
	}

	async function addRule() {
		if (!newRule.pattern || !newRule.assigned_category) {
			toasts.trigger('Please fill in all required fields', 'error');
			return;
		}

		try {
			loading = true;
			const res = await fetchJson('/settings/category-rules', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(newRule)
			});
			rules = [...rules, res];
			newRule = { match_type: 'sender', pattern: '', assigned_category: '', priority: 10 };
			toasts.trigger('Category rule added successfully', 'success');
		} catch {
			toasts.trigger('Error adding category rule', 'error');
		} finally {
			loading = false;
		}
	}

	async function updateRule(rule: CategoryRule) {
		if (!rule.id) return;

		try {
			loading = true;
			const res = await fetchJson(`/settings/category-rules/${rule.id}`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(rule)
			});
			rules = rules.map((r) => (r.id === rule.id ? res : r));
			editingRule = null;
			toasts.trigger('Category rule updated successfully', 'success');
		} catch {
			toasts.trigger('Error updating category rule', 'error');
		} finally {
			loading = false;
		}
	}

	function startEdit(rule: CategoryRule) {
		editingRule = { ...rule };
	}

	function cancelEdit() {
		editingRule = null;
	}

	function deleteRule(id: number) {
		ruleToDelete = id;
		showDeleteConfirm = true;
	}

	async function handleConfirmDelete() {
		if (ruleToDelete === null) return;
		showDeleteConfirm = false;
		try {
			await fetchJson(`/settings/category-rules/${ruleToDelete}`, { method: 'DELETE' });
			rules = rules.filter((r) => r.id !== ruleToDelete);
			toasts.trigger('Category rule deleted', 'success');
		} catch {
			toasts.trigger('Error deleting category rule', 'error');
		} finally {
			ruleToDelete = null;
		}
	}

	function handleCancelDelete() {
		showDeleteConfirm = false;
		ruleToDelete = null;
	}
</script>

<div class="card">
	<div class="mb-4">
		<p class="text-sm text-text-secondary dark:text-text-secondary-dark mb-2">
			Define rules to automatically categorize receipts based on sender or subject patterns. Higher
			priority rules are matched first.
		</p>
	</div>

	<!-- Add New Rule Form -->
	<div class="mb-6 p-4 bg-background-secondary dark:bg-background-secondary-dark rounded-lg">
		<h4 class="font-semibold mb-3 text-text-main dark:text-text-main-dark">Add New Rule</h4>
		<div class="grid gap-4 md:grid-cols-2">
			<div>
				<label for="new-match-type" class="block text-sm font-medium text-text-main dark:text-text-main-dark mb-1">
					Match Type
				</label>
				<select
					id="new-match-type"
					bind:value={newRule.match_type}
					class="input w-full"
					disabled={loading}
				>
					<option value="sender">Sender</option>
					<option value="subject">Subject</option>
				</select>
			</div>
			<div>
				<label for="new-pattern" class="block text-sm font-medium text-text-main dark:text-text-main-dark mb-1">
					Pattern (supports wildcards like *@uber.com)
				</label>
				<input
					id="new-pattern"
					type="text"
					bind:value={newRule.pattern}
					placeholder="e.g., *@uber.com"
					class="input w-full"
					disabled={loading}
				/>
			</div>
			<div>
				<label for="new-category" class="block text-sm font-medium text-text-main dark:text-text-main-dark mb-1">
					Category
				</label>
				<input
					id="new-category"
					type="text"
					bind:value={newRule.assigned_category}
					placeholder="e.g., Travel"
					class="input w-full"
					disabled={loading}
				/>
			</div>
			<div>
				<label for="new-priority" class="block text-sm font-medium text-text-main dark:text-text-main-dark mb-1">
					Priority (higher = checked first)
				</label>
				<input
					id="new-priority"
					type="number"
					bind:value={newRule.priority}
					min="1"
					max="100"
					class="input w-full"
					disabled={loading}
				/>
			</div>
		</div>
		<button
			onclick={addRule}
			class="btn btn-primary mt-4 flex items-center gap-2"
			disabled={loading}
		>
			<Plus size={16} />
			Add Rule
		</button>
	</div>

	<!-- Rules List -->
	{#if rules.length === 0}
		<div class="text-center py-8 text-text-secondary dark:text-text-secondary-dark">
			<p>No category rules yet. Add one above to get started.</p>
		</div>
	{:else}
		<div class="space-y-2">
			{#each rules as rule (rule.id)}
				<div
					class="p-4 border border-border dark:border-border-dark rounded-lg hover:bg-background-secondary dark:hover:bg-background-secondary-dark transition-colors"
				>
					{#if editingRule && editingRule.id === rule.id}
						<!-- Edit Mode -->
						<div class="grid gap-4 md:grid-cols-2">
							<div>
								<label for="edit-match-type-{rule.id}" class="block text-sm font-medium text-text-main dark:text-text-main-dark mb-1">
									Match Type
								</label>
								<select
									id="edit-match-type-{rule.id}"
									bind:value={editingRule.match_type}
									class="input w-full"
									disabled={loading}
								>
									<option value="sender">Sender</option>
									<option value="subject">Subject</option>
								</select>
							</div>
							<div>
								<label for="edit-pattern-{rule.id}" class="block text-sm font-medium text-text-main dark:text-text-main-dark mb-1">
									Pattern
								</label>
								<input
									id="edit-pattern-{rule.id}"
									type="text"
									bind:value={editingRule.pattern}
									class="input w-full"
									disabled={loading}
								/>
							</div>
							<div>
								<label for="edit-category-{rule.id}" class="block text-sm font-medium text-text-main dark:text-text-main-dark mb-1">
									Category
								</label>
								<input
									id="edit-category-{rule.id}"
									type="text"
									bind:value={editingRule.assigned_category}
									class="input w-full"
									disabled={loading}
								/>
							</div>
							<div>
								<label for="edit-priority-{rule.id}" class="block text-sm font-medium text-text-main dark:text-text-main-dark mb-1">
									Priority
								</label>
								<input
									id="edit-priority-{rule.id}"
									type="number"
									bind:value={editingRule.priority}
									min="1"
									max="100"
									class="input w-full"
									disabled={loading}
								/>
							</div>
						</div>
						<div class="flex gap-2 mt-4">
							<button
								onclick={() => updateRule(editingRule!)}
								class="btn btn-primary"
								disabled={loading}
							>
								Save
							</button>
							<button onclick={cancelEdit} class="btn btn-secondary" disabled={loading}>
								Cancel
							</button>
						</div>
					{:else}
						<!-- View Mode -->
						<div class="flex items-start justify-between">
							<div class="flex-1">
								<div class="flex items-center gap-2 mb-2">
									<span
										class="px-2 py-1 text-xs font-semibold rounded bg-primary text-white dark:bg-primary-dark"
									>
										{rule.match_type}
									</span>
									<span
										class="px-2 py-1 text-xs font-semibold rounded bg-secondary text-text-main dark:bg-secondary-dark"
									>
										Priority: {rule.priority}
									</span>
								</div>
								<p class="text-text-main dark:text-text-main-dark font-medium">
									Pattern: <span class="font-mono text-sm">{rule.pattern}</span>
								</p>
								<p class="text-text-secondary dark:text-text-secondary-dark text-sm mt-1">
									Category: <span class="font-semibold">{rule.assigned_category}</span>
								</p>
							</div>
							<div class="flex gap-2">
								<button
									onclick={() => startEdit(rule)}
									class="btn-icon"
									aria-label="Edit rule"
									disabled={loading}
								>
									<Edit2 size={16} />
								</button>
								<button
									onclick={() => deleteRule(rule.id!)}
									class="btn-icon btn-danger"
									aria-label="Delete rule"
									disabled={loading}
								>
									<Trash2 size={16} />
								</button>
							</div>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>

<ConfirmDialog
	bind:isOpen={showDeleteConfirm}
	title="Delete Category Rule"
	message="Are you sure you want to delete this category rule? This action cannot be undone."
	onConfirm={handleConfirmDelete}
	onCancel={handleCancelDelete}
/>
