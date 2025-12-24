<script lang="ts">
	import { LayoutDashboard, Settings, History, ShieldCheck, Sliders } from 'lucide-svelte';

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
				class="h-10 md:h-14 w-auto border-2 border-primary bg-white rounded-lg shadow-sm"
			/>
			<span class="hidden md:inline text-xs font-mono text-gray-400 mt-2">v{__APP_VERSION__}</span>
		</button>

		<!-- Desktop Navigation Links -->
		<div
			class="hidden md:flex items-center gap-1 bg-gray-100/50 p-1 rounded-xl border border-gray-200/50"
		>
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
				'preferences'
					? 'bg-white text-primary shadow-sm ring-1 ring-black/5'
					: 'text-text-secondary hover:text-primary hover:bg-gray-100'}"
				onclick={() => onViewChange('preferences')}
			>
				<Sliders size={18} />
				Preferences
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

<!-- Mobile Bottom Navigation -->
<div
	class="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-white/90 backdrop-blur-xl border-t border-gray-200 pb-safe shadow-[0_-8px_30px_rgb(0,0,0,0.04)]"
>
	<div class="flex items-center justify-around h-16 px-2">
		<button
			class="flex flex-col items-center gap-1 flex-1 py-1 transition-all {currentView ===
			'dashboard'
				? 'text-primary'
				: 'text-gray-400'}"
			onclick={() => onViewChange('dashboard')}
		>
			<LayoutDashboard size={20} class={currentView === 'dashboard' ? 'scale-110' : ''} />
			<span class="text-[10px] font-medium">Home</span>
		</button>

		<button
			class="flex flex-col items-center gap-1 flex-1 py-1 transition-all {currentView === 'history'
				? 'text-primary'
				: 'text-gray-400'}"
			onclick={() => onViewChange('history')}
		>
			<History size={20} class={currentView === 'history' ? 'scale-110' : ''} />
			<span class="text-[10px] font-medium">History</span>
		</button>

		<button
			class="flex flex-col items-center gap-1 flex-1 py-1 transition-all {currentView === 'rules'
				? 'text-primary'
				: 'text-gray-400'}"
			onclick={() => onViewChange('rules')}
		>
			<ShieldCheck size={20} class={currentView === 'rules' ? 'scale-110' : ''} />
			<span class="text-[10px] font-medium">Rules</span>
		</button>

		<button
			class="flex flex-col items-center gap-1 flex-1 py-1 transition-all {currentView ===
			'preferences'
				? 'text-primary'
				: 'text-gray-400'}"
			onclick={() => onViewChange('preferences')}
		>
			<Sliders size={20} class={currentView === 'preferences' ? 'scale-110' : ''} />
			<span class="text-[10px] font-medium">Prefs</span>
		</button>

		<button
			class="flex flex-col items-center gap-1 flex-1 py-1 transition-all {currentView === 'settings'
				? 'text-primary'
				: 'text-gray-400'}"
			onclick={() => onViewChange('settings')}
		>
			<Settings size={20} class={currentView === 'settings' ? 'scale-110' : ''} />
			<span class="text-[10px] font-medium">Settings</span>
		</button>
	</div>
</div>
