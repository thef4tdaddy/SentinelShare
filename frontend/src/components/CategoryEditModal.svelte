<script lang="ts">
	import Modal from './Modal.svelte';
	import { fetchJson } from '../lib/api';
	import { toasts } from '../lib/stores/toast';
	import { Tag } from 'lucide-svelte';

	interface CategoryEditModalProps {
		isOpen: boolean;
		emailId: number | null;
		currentCategory: string;
		sender: string;
		subject: string;
		onClose: () => void;
		onSuccess: () => void;
	}

	let {
		isOpen = $bindable(),
		emailId,
		currentCategory,
		sender,
		subject,
		onClose,
		onSuccess
	}: CategoryEditModalProps = $props();

	let newCategory = $state('');
	let createRule = $state(false);
	let matchType = $state<'sender' | 'subject'>('sender');
	let loading = $state(false);

	// Reset form when modal opens or currentCategory changes
	$effect(() => {
		if (isOpen) {
			newCategory = currentCategory;
			createRule = false;
			matchType = 'sender';
		}
	});

	async function handleSave() {
		const trimmedCategory = newCategory.trim();
		
		if (!emailId || !trimmedCategory) {
			toasts.trigger('Please enter a category', 'error');
			return;
		}

		try {
			loading = true;
			const res = await fetchJson(`/api/history/emails/${emailId}/category`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					category: trimmedCategory,
					create_rule: createRule,
					match_type: matchType
				})
			});

			toasts.trigger(res.message || 'Category updated successfully', 'success');
			onSuccess();
			onClose();
		} catch {
			toasts.trigger('Failed to update category', 'error');
		} finally {
			loading = false;
		}
	}

	function handleCancel() {
		onClose();
	}
</script>

<Modal {isOpen} onClose={handleCancel} title="Edit Category">
	<div class="space-y-4">
		<div>
			<label for="category-input" class="block text-sm font-medium text-text-main dark:text-text-main-dark mb-2">
				Category
			</label>
			<input
				id="category-input"
				type="text"
				bind:value={newCategory}
				placeholder="e.g., Travel, Food, Shopping"
				class="input w-full"
				disabled={loading}
			/>
		</div>

		<div class="bg-background-secondary dark:bg-background-secondary-dark p-4 rounded-lg">
			<h4 class="text-sm font-semibold text-text-main dark:text-text-main-dark mb-3 flex items-center gap-2">
				<Tag size={16} />
				Smart Suggestion
			</h4>
			<p class="text-xs text-text-secondary dark:text-text-secondary-dark mb-3">
				Would you like to automatically categorize similar emails in the future?
			</p>

			<label class="flex items-start gap-2 cursor-pointer">
				<input
					type="checkbox"
					bind:checked={createRule}
					class="mt-1"
					disabled={loading}
				/>
				<div class="flex-1">
					<span class="text-sm text-text-main dark:text-text-main-dark">
						Create a rule for future categorization
					</span>
					<p class="text-xs text-text-secondary dark:text-text-secondary-dark mt-1">
						This will automatically categorize similar emails as "{newCategory}"
					</p>
				</div>
			</label>

			{#if createRule}
				<div class="mt-3 pl-6 space-y-2">
					<label class="flex items-center gap-2 cursor-pointer">
						<input
							type="radio"
							bind:group={matchType}
							value="sender"
							disabled={loading}
						/>
						<div>
							<span class="text-sm text-text-main dark:text-text-main-dark">Match by sender</span>
							<p class="text-xs text-text-secondary dark:text-text-secondary-dark">
								Categorize all emails from <span class="font-mono">{sender}</span>
							</p>
						</div>
					</label>

					<label class="flex items-center gap-2 cursor-pointer">
						<input
							type="radio"
							bind:group={matchType}
							value="subject"
							disabled={loading}
						/>
						<div>
							<span class="text-sm text-text-main dark:text-text-main-dark">Match by subject</span>
							<p class="text-xs text-text-secondary dark:text-text-secondary-dark">
								Categorize emails with similar subject: <span class="font-mono">{subject}</span>
							</p>
						</div>
					</label>
				</div>
			{/if}
		</div>

		<div class="flex gap-3 justify-end pt-4">
			<button onclick={handleCancel} class="btn btn-secondary" disabled={loading}>
				Cancel
			</button>
			<button onclick={handleSave} class="btn btn-primary" disabled={loading}>
				{loading ? 'Saving...' : 'Save'}
			</button>
		</div>
	</div>
</Modal>
