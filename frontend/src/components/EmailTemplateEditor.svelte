<script lang="ts">
	import { fetchJson } from '../lib/api';
	import { onMount } from 'svelte';
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
			alert('Template saved successfully!');
		} catch {
			alert('Error saving template');
		} finally {
			saving = false;
		}
	}

	function togglePreview() {
		if (showPreview) {
			showPreview = false;
		} else {
			// Generate a preview with sample data
			previewText = template
				.replace(/{subject}/g, 'Your Amazon Order Confirmation')
				.replace(/{from}/g, 'no-reply@amazon.com')
				.replace(
					/{body}/g,
					'Thank you for your order!\n\nOrder #123-4567890-1234567\nTotal: $49.99\n\nYour order will be delivered on January 15, 2024.'
				);
			showPreview = true;
		}
	}

	$: hasChanges = template !== originalTemplate;
</script>

<div class="card">
	<div class="p-6">
		<div class="mb-6">
			<h4 class="text-lg font-bold text-text-main mb-2">Email Template</h4>
			<p class="text-sm text-text-secondary">
				Customize how forwarded emails appear. Use variables like <code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600"
					>{'{subject}'}</code
				>,
				<code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600">{'{from}'}</code>, and
				<code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600">{'{body}'}</code> to insert email content.
			</p>
		</div>

		{#if loading}
			<div class="text-center py-8 text-text-secondary">Loading template...</div>
		{:else}
			<div class="space-y-4">
				<!-- Template Editor -->
				<div>
					<label for="template" class="block text-sm font-medium text-text-secondary mb-2">
						Template Content
					</label>
					<textarea
						id="template"
						bind:value={template}
						rows="10"
						class="input-field font-mono text-sm"
						placeholder="Enter your email template..."
					></textarea>
				</div>

				<!-- Available Variables -->
				<div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
					<p class="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
						Available Variables
					</p>
					<div class="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
						<div>
							<code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600">{'{subject}'}</code>
							<span class="text-text-secondary ml-1">- Email subject</span>
						</div>
						<div>
							<code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600">{'{from}'}</code>
							<span class="text-text-secondary ml-1">- Sender email</span>
						</div>
						<div>
							<code class="bg-gray-100 text-sm px-2 py-0.5 rounded font-mono text-blue-600">{'{body}'}</code>
							<span class="text-text-secondary ml-1">- Email body</span>
						</div>
					</div>
				</div>

				<!-- Preview Section -->
				{#if showPreview}
					<div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
						<p class="text-xs font-semibold text-blue-900 uppercase tracking-wider mb-2">
							Preview (with sample data)
						</p>
						<pre class="text-sm text-text-main whitespace-pre-wrap font-sans">{previewText}</pre>
					</div>
				{/if}

				<!-- Action Buttons -->
				<div class="flex gap-3 pt-2">
					<button
						on:click={saveTemplate}
						disabled={saving || !hasChanges}
						class="btn btn-primary"
					>
						<Save size={16} />
						{saving ? 'Saving...' : 'Save Template'}
					</button>

					<button on:click={togglePreview} class="btn btn-secondary">
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
