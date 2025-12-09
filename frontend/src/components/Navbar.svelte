<script lang="ts">
	import { LayoutDashboard, Settings, Shield } from 'lucide-svelte';

	export let currentView: string;
	export let onViewChange: (view: string) => void;
</script>

<nav
	class="sticky top-0 z-50 w-full backdrop-blur-md bg-white/70 border-b border-border transition-all duration-300"
>
	<div class="container-custom flex items-center justify-between h-16">
		<!-- Logo Section -->
		<div
			class="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
			on:click={() => onViewChange('dashboard')}
		>
			<img
				src="/assets/LogoWithText.svg"
				alt="SentinelShare"
				class="h-12 w-auto border-2 border-primary/20 bg-white rounded-lg p-0.5 shadow-sm"
			/>
		</div>

		<!-- Navigation Links -->
		<div class="flex items-center gap-1 bg-gray-100/50 p-1 rounded-xl border border-gray-200/50">
			<button
				class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 {currentView ===
				'dashboard'
					? 'bg-white text-primary shadow-sm ring-1 ring-black/5'
					: 'text-text-secondary hover:text-primary hover:bg-gray-100'}"
				on:click={() => onViewChange('dashboard')}
			>
				<LayoutDashboard size={18} />
				Dashboard
			</button>

			<button
				class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 {currentView ===
				'settings'
					? 'bg-white text-primary shadow-sm ring-1 ring-black/5'
					: 'text-text-secondary hover:text-primary hover:bg-gray-100'}"
				on:click={() => onViewChange('settings')}
			>
				<Settings size={18} />
				Settings
			</button>
		</div>
	</div>
</nav>
