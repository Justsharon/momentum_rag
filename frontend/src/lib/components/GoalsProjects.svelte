<script lang="ts">
  interface Goal {
    title: string;
    status: string;
  }

  interface Project {
    name: string;
    status: string;
    next_step: string;
  }

   let { 
    goals = [],
    projects = []
   }:{
    goals: Goal[];
    projects: Project[]
   } = $props();

  const statusColor: Record<string, string> = {
    active: 'text-spark', in_progress: 'text-spark',
    done: 'text-calm', completed: 'text-calm',
    on_hold: 'text-muted', paused: 'text-muted',
    not_started: 'text-muted',
  };
</script>

<div class="bg-panel rounded-lg p-5 border border-white/5">
  <h2 class="font-display text-lg text-ink mb-4">Goals & projects</h2>

  {#if projects.length === 0 && goals.length === 0}
    <p class="text-muted text-sm">Nothing here yet. Add goals and projects via seed.py or the API.</p>
  {/if}

  {#if projects.length}
    <div class="mb-4">
      <p class="text-xs uppercase tracking-wide text-muted font-mono mb-2">Projects</p>
      <ul class="space-y-2">
        {#each projects as p (p)}
          <li class="text-sm">
            <div class="flex items-center justify-between">
              <span class="text-ink font-medium">{p.name}</span>
              <span class="text-xs font-mono {statusColor[p.status as string] || 'text-muted'}">{p.status}</span>
            </div>
            <p class="text-muted text-xs mt-0.5">Next: {p.next_step}</p>
          </li>
        {/each}
      </ul>
    </div>
  {/if}

  {#if goals.length}
    <div>
      <p class="text-xs uppercase tracking-wide text-muted font-mono mb-2">Goals</p>
      <ul class="space-y-2">
        {#each goals as g (g)}
          <li class="text-sm">
            <div class="flex items-center justify-between">
              <span class="text-ink font-medium">{g.title}</span>
              <span class="text-xs font-mono {statusColor[g.status as string] || 'text-muted'}">{g.status}</span>
            </div>
          </li>
        {/each}
      </ul>
    </div>
  {/if}
</div>