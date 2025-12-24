<script lang="ts">
	import { toasts } from '../lib/stores/toast';
	import { X, CheckCircle, AlertCircle, Info } from 'lucide-svelte';
	import { fly } from 'svelte/transition';
	import { flip } from 'svelte/animate';
</script>

<div class="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
	{#each $toasts as toast (toast.id)}
		<div
			class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border backdrop-blur-xl min-w-[300px] max-w-sm"
			class:bg-emerald-50={toast.type === 'success'}
			class:border-emerald-100={toast.type === 'success'}
			class:bg-red-50={toast.type === 'error'}
			class:border-red-100={toast.type === 'error'}
			class:bg-blue-50={toast.type === 'info'}
			class:border-blue-100={toast.type === 'info'}
			in:fly={{ y: 20, duration: 300 }}
			out:fly={{ x: 20, duration: 200 }}
			animate:flip
		>
			<div class="shrink-0">
				{#if toast.type === 'success'}
					<CheckCircle class="text-emerald-500" size={20} />
				{:else if toast.type === 'error'}
					<AlertCircle class="text-red-500" size={20} />
				{:else}
					<Info class="text-blue-500" size={20} />
				{/if}
			</div>

			<p
				class="text-sm font-medium flex-1 leading-snug"
				class:text-emerald-900={toast.type === 'success'}
				class:text-red-900={toast.type === 'error'}
				class:text-blue-900={toast.type === 'info'}
			>
				{toast.message}
			</p>

			<button
				class="p-1 rounded-lg hover:bg-black/5 transition-colors"
				onclick={() => toasts.remove(toast.id)}
				aria-label="Close notification"
			>
				<X size={16} class="opacity-40 hover:opacity-100 transition-opacity" />
			</button>
		</div>
	{/each}
</div>
