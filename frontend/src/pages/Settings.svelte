<script lang="ts">
  import PreferenceList from '../components/PreferenceList.svelte';
</script>

<h1>Settings</h1>
<p style="color: var(--text-secondary); margin-bottom: 2rem;">Manage your detection rules and preferences.</p>

<PreferenceList type="preferences" />
<PreferenceList type="rules" />
