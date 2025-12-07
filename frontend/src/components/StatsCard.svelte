<script lang="ts">
  export let title: string;
  export let value: string | number;
  export let subtext: string = '';
</script>

<div class="card">
  <div style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.5rem; text-transform: uppercase; font-weight: 600;">
    {title}
  </div>
  <div style="font-size: 2rem; font-weight: bold; color: var(--primary);">
    {value}
  </div>
  {#if subtext}
    <div style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.25rem;">
      {subtext}
    </div>
  {/if}
</div>
