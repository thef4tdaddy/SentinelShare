<script lang="ts">
	import type { ComponentType } from 'svelte';

	export let title: string;
	export let value: string | number;
	export let subtext: string = '';
	// Accept an icon component (not just a string)
	export let icon: ComponentType | null = null;
	export let variant: 'default' | 'success' | 'danger' = 'default';

	const variantColors = {
		default: 'bg-blue-50 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400',
		success: 'bg-green-50 text-green-600 dark:bg-green-900/50 dark:text-green-400',
		danger: 'bg-red-50 text-red-600 dark:bg-red-900/50 dark:text-red-400'
	};
</script>

<div class="card flex flex-col justify-between h-full group">
	<div class="flex items-start justify-between mb-4">
		<div>
			<p class="text-xs font-semibold uppercase tracking-wider text-text-secondary mb-1 dark:text-text-secondary-dark">{title}</p>
			<h3
				class="text-3xl font-bold text-text-main tracking-tight group-hover:text-primary transition-colors dark:text-text-main-dark dark:group-hover:text-primary-dark"
			>
				{value}
			</h3>
		</div>

		{#if icon}
			<div
				class="p-3 rounded-xl {variantColors[
					variant
				]} shadow-sm group-hover:scale-110 transition-transform duration-200"
			>
				<svelte:component this={icon} size={20} />
			</div>
		{/if}
	</div>

	{#if subtext}
		<div
			class="text-xs font-medium text-text-secondary flex items-center gap-1.5 pt-4 border-t border-gray-50 dark:text-text-secondary-dark dark:border-gray-700"
		>
			{subtext}
		</div>
	{/if}
</div>
