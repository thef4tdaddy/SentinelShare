<script lang="ts">
	import { onMount } from 'svelte';
	import Navbar from './components/Navbar.svelte';
	import Dashboard from './pages/Dashboard.svelte';
	import History from './pages/History.svelte';
	import Rules from './pages/Rules.svelte';
	import Settings from './pages/Settings.svelte';
	import Login from './pages/Login.svelte';
	import SendeeDashboard from './pages/SendeeDashboard.svelte';
	import Toast from './components/Toast.svelte';
	import './app.css';

	let currentView = 'loading';
	let dashboardToken: string | null = null;

	onMount(async () => {
		// Check for token in URL first (Sendee access)
		const params = new URLSearchParams(window.location.search);
		const token = params.get('token');
		if (token) {
			dashboardToken = token;
			currentView = 'sendee';
			return;
		}

		try {
			const res = await fetch('/api/auth/me');
			if (res.ok) {
				currentView = 'dashboard';
			} else {
				currentView = 'login';
			}
		} catch (e) {
			console.error('Auth check failed', e);
			currentView = 'login';
		}
	});

	function handleViewChange(view: string) {
		currentView = view;
	}

	function handleLoginSuccess() {
		currentView = 'dashboard';
	}
</script>

<main class="min-h-screen bg-gray-50">
	{#if currentView === 'loading'}
		<div class="h-screen flex items-center justify-center">
			<span class="loading loading-spinner loading-lg text-primary"></span>
		</div>
	{:else if currentView === 'login'}
		<Login onLoginSuccess={handleLoginSuccess} />
	{:else}
		<Navbar {currentView} onViewChange={handleViewChange} />

		<div class="container-custom">
			{#if currentView === 'dashboard'}
				<Dashboard />
			{:else if currentView === 'history'}
				<History />
			{:else if currentView === 'rules'}
				<Rules />
			{:else if currentView === 'preferences'}
				<SendeeDashboard isAdmin={true} />
			{:else if currentView === 'sendee'}
				<SendeeDashboard token={dashboardToken} isAdmin={false} />
			{:else if currentView === 'settings'}
				<Settings />
			{/if}
		</div>
	{/if}
	<Toast />
</main>
