<script lang="ts">
  import Navbar from './components/Navbar.svelte';
  import Dashboard from './pages/Dashboard.svelte';
  import Settings from './pages/Settings.svelte';
  import './app.css';

  let currentView = 'dashboard';

  function handleViewChange(view: string) {
    currentView = view;
  }
</script>

<main>
  <Navbar {currentView} onViewChange={handleViewChange} />
  
  <div class="container">
    {#if currentView === 'dashboard'}
      <Dashboard />
    {:else if currentView === 'settings'}
      <Settings />
    {/if}
  </div>
</main>
