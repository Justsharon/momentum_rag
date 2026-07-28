<script lang="ts">
  import { onMount } from 'svelte';
  
  import CheckInForm from '$lib/components/CheckInForm.svelte';
  import AskPanel from '$lib/components/AskPanel.svelte';
  import GoalsProjects from '$lib/components/GoalsProjects.svelte';
  import { getRecentCheckIns, getGoals, getProjects } from '$lib/models/api';
	import MomentumGrid from '$lib/components/MomentumGrid.svelte';

  let checkins = $state([]);
  let goals = $state([]);
  let projects = $state([]);
  let loadError: string | null = $state(null);

  async function loadData() {
    try {
      [checkins, goals, projects] = await Promise.all([
        getRecentCheckIns(84),
        getGoals(),
        getProjects(),
      ]);
    } catch (e) {
      loadError = e instanceof Error ? e.message : String(e);
    }
  }

  onMount(loadData);
</script>

<main class="min-h-screen bg-graphite font-body">
  <div class="max-w-4xl mx-auto px-6 py-10">
    <header class="mb-8">
      <h1 class="font-display text-3xl text-ink tracking-tight">MomentumRAG</h1>
      <p class="text-muted text-sm mt-1">A memory for your goals, so a slow week doesn't erase six good months.</p>
    </header>

    {#if loadError}
      <p class="text-rust text-sm mb-4">Couldn't reach the API: {loadError}. Is it running on port 8000?</p>
    {/if}

    <section class="bg-panel rounded-lg p-5 border border-white/5 mb-6">
      <MomentumGrid {checkins} />
    </section>

    <div class="grid md:grid-cols-2 gap-6 mb-6">
      <CheckInForm on:saved={loadData} />
      <GoalsProjects {goals} {projects} />
    </div>

    <AskPanel />
  </div>
</main>