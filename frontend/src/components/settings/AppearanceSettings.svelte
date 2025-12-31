<script lang="ts">
	import { Sun, Moon } from 'lucide-svelte';
	import { theme as themeStore } from '../../lib/stores/theme';

	const currentTheme = $derived($themeStore);

	function toggleTheme() {
		themeStore.toggle();
	}
</script>

<section>
	<h3 class="text-lg font-bold text-text-main mb-4 dark:text-text-main-dark">Appearance</h3>
	<div class="card">
		<div class="flex items-center justify-between">
			<div>
				<p class="font-medium text-text-main dark:text-text-main-dark">Dark Mode</p>
				<p class="text-sm text-text-secondary dark:text-text-secondary-dark">
					Toggle between light and dark theme
				</p>
			</div>
			<button
				onclick={toggleTheme}
				class="btn btn-secondary flex items-center gap-2"
				aria-label="Toggle theme"
			>
				{#if currentTheme === 'dark'}
					<Sun size={18} />
					Light
				{:else}
					<Moon size={18} />
					Dark
				{/if}
			</button>
		</div>
	</div>
</section>
