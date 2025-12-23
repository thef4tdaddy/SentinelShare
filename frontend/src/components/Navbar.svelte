<script lang="ts">
	import { LayoutDashboard, Settings, History, ShieldCheck } from 'lucide-svelte';

	export let currentView: string;
	export let onViewChange: (view: string) => void;
</script>

<nav
	class="sticky top-0 z-50 w-full backdrop-blur-md bg-white/70 border-b border-border transition-all duration-300"
>
	<div class="container-custom flex items-center justify-between h-16">
		<!-- Logo Section -->
		<button
			class="flex items-center gap-2 hover:opacity-80 transition-opacity border-none bg-transparent p-0 cursor-pointer"
			onclick={() => onViewChange('dashboard')}
			aria-label="Go to Dashboard"
		>
			<img
				src="/assets/LogoWithText.svg"
				alt="SentinelShare Logo"
				class="h-14 w-auto border-2 border-primary bg-white rounded-lg shadow-sm"
			/>
			<span class="text-xs font-mono text-gray-400 mt-2">v{__APP_VERSION__}</span>
		</button>

		<!-- Navigation Links -->
		<div class="flex items-center gap-1 bg-gray-100/50 p-1 rounded-xl border border-gray-200/50">
			<button
				class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 {currentView ===
				'dashboard'
					? 'bg-white text-primary shadow-sm ring-1 ring-black/5'
					: 'text-text-secondary hover:text-primary hover:bg-gray-100'}"
				onclick={() => onViewChange('dashboard')}
			>
				<LayoutDashboard size={18} />
				Dashboard
			</button>

			<button
				class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 {currentView ===
				'history'
					? 'bg-white text-primary shadow-sm ring-1 ring-black/5'
					: 'text-text-secondary hover:text-primary hover:bg-gray-100'}"
				onclick={() => onViewChange('history')}
			>
				<History size={18} />
				History
			</button>

			<button
				class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 {currentView ===
				'rules'
					? 'bg-white text-primary shadow-sm ring-1 ring-black/5'
					: 'text-text-secondary hover:text-primary hover:bg-gray-100'}"
				onclick={() => onViewChange('rules')}
			>
				<ShieldCheck size={18} />
				Rules
			</button>

			<button
				class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 {currentView ===
				'settings'
					? 'bg-white text-primary shadow-sm ring-1 ring-black/5'
					: 'text-text-secondary hover:text-primary hover:bg-gray-100'}"
				onclick={() => onViewChange('settings')}
			>
				<Settings size={18} />
				Settings
			</button>
		</div>
	</div>
</nav>
