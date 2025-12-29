<script lang="ts">
	import { toasts } from '../lib/stores/toast';
	import { X, CheckCircle, AlertCircle, Info } from 'lucide-svelte';
	import { fly } from 'svelte/transition';
	import { flip } from 'svelte/animate';
	import type { ToastType } from '../lib/stores/toast';

	// Theme-aware class configurations for better maintainability
	const toastThemes = {
		success: {
			container: 'bg-emerald-50 border-emerald-100 dark:bg-emerald-900/50 dark:border-emerald-800',
			icon: 'text-emerald-500 dark:text-emerald-400',
			text: 'text-emerald-900 dark:text-emerald-100'
		},
		error: {
			container: 'bg-red-50 border-red-100 dark:bg-red-900/50 dark:border-red-800',
			icon: 'text-red-500 dark:text-red-400',
			text: 'text-red-900 dark:text-red-100'
		},
		info: {
			container: 'bg-blue-50 border-blue-100 dark:bg-blue-900/50 dark:border-blue-800',
			icon: 'text-blue-500 dark:text-blue-400',
			text: 'text-blue-900 dark:text-blue-100'
		}
	} as const;

	function getToastTheme(type: ToastType) {
		return toastThemes[type];
	}
</script>

<div class="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
	{#each $toasts as toast (toast.id)}
		<div
			class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border backdrop-blur-xl min-w-[300px] max-w-sm {getToastTheme(toast.type).container}"
			in:fly={{ y: 20, duration: 300 }}
			out:fly={{ x: 20, duration: 200 }}
			animate:flip
		>
			<div class="shrink-0">
				{#if toast.type === 'success'}
					<CheckCircle class={getToastTheme(toast.type).icon} size={20} />
				{:else if toast.type === 'error'}
					<AlertCircle class={getToastTheme(toast.type).icon} size={20} />
				{:else}
					<Info class={getToastTheme(toast.type).icon} size={20} />
				{/if}
			</div>

			<p class="text-sm font-medium flex-1 leading-snug {getToastTheme(toast.type).text}">
				{toast.message}
			</p>

			<button
				class="p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
				onclick={() => toasts.remove(toast.id)}
				aria-label="Close notification"
			>
				<X size={16} class="opacity-40 hover:opacity-100 transition-opacity" />
			</button>
		</div>
	{/each}
</div>
