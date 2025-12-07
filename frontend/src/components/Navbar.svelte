<script lang="ts">
  export let currentView: string;
  export let onViewChange: (view: string) => void;
</script>

<nav class="nav">
  <div class="container nav-content">
    <div style="font-weight: bold; font-size: 1.25rem;">Receipt Forwarder</div>
    <div class="nav-links">
      <button 
        class:active={currentView === 'dashboard'} 
        on:click={() => onViewChange('dashboard')}>
        Dashboard
      </button>
      <button 
        class:active={currentView === 'settings'} 
        on:click={() => onViewChange('settings')}>
        Settings
      </button>
    </div>
  </div>
</nav>
