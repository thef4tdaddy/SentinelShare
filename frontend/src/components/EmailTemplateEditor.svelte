<script lang="ts">
	import { fetchJson } from '../lib/api';
	import DOMPurify from 'dompurify';
	import { onMount } from 'svelte';
	import { toasts } from '../lib/stores/toast';
	import { Save, Eye, EyeOff } from 'lucide-svelte';

	let template = '';
	let originalTemplate = '';
	let loading = false;
	let saving = false;
	let showPreview = false;
	let previewText = '';

	onMount(loadTemplate);

	async function loadTemplate() {
		try {
			loading = true;
			const res = await fetchJson('/settings/email-template');
			template = res.template || '';
			originalTemplate = template;
		} catch {
			console.error('Error loading template');
			toasts.trigger('Error loading template', 'error');
		} finally {
			loading = false;
		}
	}

	async function saveTemplate() {
		try {
			saving = true;
			await fetchJson('/settings/email-template', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ template })
			});
			originalTemplate = template;
			toasts.trigger('Template saved successfully!', 'success');
		} catch {
			toasts.trigger('Error saving template', 'error');
		} finally {
			saving = false;
		}
	}

	function togglePreview() {
		if (showPreview) {
			showPreview = false;
		} else {
			// Generate a preview with sample data
			const rawPreview = template
				.replace(/{subject}/g, 'Your Amazon Order Confirmation')
				.replace(/{from}/g, 'no-reply@amazon.com')
				.replace(/{simple_name}/g, 'Amazon')
				.replace(/{link_stop}/g, '#stop')
				.replace(/{link_more}/g, '#more')
				.replace(/{link_settings}/g, '#settings')
				.replace(/{action_type_text}/g, 'Clicking an action opens a web confirmation.')
				.replace(
					/{body}/g,
					'Thank you for your order!\n\nOrder #123-4567890-1234567\nTotal: $49.99\n\nYour order will be delivered on January 15, 2024.'
				);

			// Sanitize HTML to prevent XSS (CI fix)
			previewText = DOMPurify.sanitize(rawPreview);
			showPreview = true;
		}
	}

	$: hasChanges = template !== originalTemplate;
</script>

<div class="card">
	<div class="p-6">
		<div class="mb-6">
			<p class="text-sm text-text-secondary dark:text-text-secondary-dark">
				Customize how forwarded emails appear. You can write full HTML here.
			</p>
		</div>

		{#if loading}
			<div class="text-center py-8 text-text-secondary dark:text-text-secondary-dark">Loading template...</div>
		{:else}
			<div class="space-y-4">
				<!-- Template Editor -->
				<div>
					<label for="template" class="block text-sm font-medium text-text-secondary mb-2">
						Template Content (HTML supported)
					</label>
					<textarea
						id="template"
						bind:value={template}
						rows="15"
						class="input-field font-mono text-xs"
						placeholder="Enter your email template..."
					></textarea>
				</div>

				<!-- Available Variables -->
				<div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
					<p class="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
						Available Variables
					</p>
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2 text-sm">
						<div>
							<code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600"
								>{'{subject}'}</code
							>
							<span class="text-text-secondary text-xs block">Email subject</span>
						</div>
						<div>
							<code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600"
								>{'{from}'}</code
							>
							<span class="text-text-secondary text-xs block">Sender email</span>
						</div>
						<div>
							<code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600"
								>{'{body}'}</code
							>
							<span class="text-text-secondary text-xs block">Email body content</span>
						</div>
						<div>
							<code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600"
								>{'{simple_name}'}</code
							>
							<span class="text-text-secondary text-xs block">E.g. "Amazon"</span>
						</div>
						<div>
							<code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600"
								>{'{link_stop}'}</code
							>
							<span class="text-text-secondary text-xs block">Block link (URL)</span>
						</div>
						<div>
							<code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600"
								>{'{link_more}'}</code
							>
							<span class="text-text-secondary text-xs block">Forward link (URL)</span>
						</div>
						<div>
							<code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600"
								>{'{link_settings}'}</code
							>
							<span class="text-text-secondary text-xs block">Settings link (URL)</span>
						</div>
					</div>
				</div>

				<!-- Preview Section -->
				{#if showPreview}
					<div class="bg-gray-100 border border-gray-200 rounded-lg p-4">
						<p class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
							Preview (with sample data)
						</p>
						<div class="bg-white p-4 rounded shadow-sm overflow-hidden prose max-w-none">
							{@html previewText}
						</div>
					</div>
				{/if}

				<!-- Action Buttons -->
				<div class="flex gap-3 pt-2">
					<button onclick={saveTemplate} disabled={saving || !hasChanges} class="btn btn-primary">
						<Save size={16} />
						{saving ? 'Saving...' : 'Save Template'}
					</button>

					<button onclick={togglePreview} class="btn btn-secondary">
						{#if showPreview}
							<EyeOff size={16} />
							Hide Preview
						{:else}
							<Eye size={16} />
							Show Preview
						{/if}
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>
