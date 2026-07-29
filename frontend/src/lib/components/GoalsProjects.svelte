<script lang="ts">
  import { createGoal, updateGoal, deleteGoal, createProject, updateProject, deleteProject } from '$lib/models/api';

  let { goals = [], projects = [], onChange = () => {} } = $props();

  const statusColor: Record<string, string> = {
    active: 'text-spark', in_progress: 'text-spark',
    done: 'text-calm', completed: 'text-calm',
    on_hold: 'text-muted', paused: 'text-muted',
    not_started: 'text-muted',
  };

  const goalStatuses = ['not_started', 'in_progress', 'completed', 'paused'];
  const projectStatuses = ['active', 'on_hold', 'done'];

  type Goal = { id: string ; status: string };
  type Project = { id: string ; status: string };

  let showGoalForm = $state(false);
  let showProjectForm = $state(false);
  let error : string | null = $state(null);

  let newGoal = $state({ title: '', description: '', why: '', priority: 3 });
  let newProject = $state({ name: '', description: '', objective: '', current_focus: '', next_step: '' });

  function getErrorMessage(err: unknown) {
    return err instanceof Error ? err.message : String(err);
  }

  async function handleGoalStatusChange(goal: Goal, newStatus: string) {
    error = null;
    try {
      await updateGoal(goal.id, { status: newStatus });
      onChange();
    } catch (err) {
      error = getErrorMessage(err);
    }
  }

  async function handleProjectStatusChange(project: Project, newStatus: string) {
    error = null;
    try {
      await updateProject(project.id, { status: newStatus });
      onChange();
    } catch (err) {
      error = getErrorMessage(err);
    }
  }

  async function handleDeleteGoal(id: string) {
    if (!confirm('Delete this goal? This can\'t be undone.')) return;
    error = null;
    try {
      await deleteGoal(id);
      onChange();
    } catch (err) {
      error = getErrorMessage(err);
    }
  }

  async function handleDeleteProject(id: string) {
    if (!confirm('Delete this project? This can\'t be undone.')) return;
    error = null;
    try {
      await deleteProject(id);
      onChange();
    } catch (err) {
      error = getErrorMessage(err);
    }
  }

  async function handleCreateGoal() {
    if (!newGoal.title.trim()) {
      error = 'Goal needs a title.';
      return;
    }
    error = null;
    try {
      await createGoal(newGoal);
      newGoal = { title: '', description: '', why: '', priority: 3 };
      showGoalForm = false;
      onChange();
    } catch (err) {
      error = getErrorMessage(err);
    }
  }

  async function handleCreateProject() {
    if (!newProject.name.trim()) {
      error = 'Project needs a name.';
      return;
    }
    error = null;
    try {
      await createProject(newProject);
      newProject = { name: '', description: '', objective: '', current_focus: '', next_step: '' };
      showProjectForm = false;
      onChange();
    } catch (err) {
      error = getErrorMessage(err);
    }
  }
</script>

<div class="bg-panel rounded-lg p-5 border border-white/5">
  <h2 class="font-display text-lg text-ink mb-4">Goals & projects</h2>

  {#if error}
    <p class="text-rust text-sm mb-3">{error}</p>
  {/if}

  {#if projects.length === 0 && goals.length === 0 && !showGoalForm && !showProjectForm}
    <p class="text-muted text-sm mb-3">Nothing here yet -- add your first one below.</p>
  {/if}

  <!-- Projects -->
  <div class="mb-5">
    <div class="flex items-center justify-between mb-2">
      <p class="text-xs uppercase tracking-wide text-muted font-mono">Projects</p>
      <button
        onclick={() => (showProjectForm = !showProjectForm)}
        class="text-xs text-calm hover:text-ink transition"
      >
        {showProjectForm ? 'Cancel' : '+ Add project'}
      </button>
    </div>

    {#if showProjectForm}
      <div class="space-y-2 mb-3 bg-graphite rounded p-3 border border-white/10">
        <input bind:value={newProject.name} placeholder="Project name"
          class="w-full bg-panel border border-white/10 rounded px-2 py-1.5 text-sm text-ink placeholder:text-muted/60" />
        <input bind:value={newProject.description} placeholder="Description"
          class="w-full bg-panel border border-white/10 rounded px-2 py-1.5 text-sm text-ink placeholder:text-muted/60" />
        <input bind:value={newProject.objective} placeholder="Objective"
          class="w-full bg-panel border border-white/10 rounded px-2 py-1.5 text-sm text-ink placeholder:text-muted/60" />
        <input bind:value={newProject.current_focus} placeholder="Current focus"
          class="w-full bg-panel border border-white/10 rounded px-2 py-1.5 text-sm text-ink placeholder:text-muted/60" />
        <input bind:value={newProject.next_step} placeholder="Next step"
          class="w-full bg-panel border border-white/10 rounded px-2 py-1.5 text-sm text-ink placeholder:text-muted/60" />
        <button onclick={handleCreateProject}
          class="w-full bg-calm text-graphite font-medium rounded py-1.5 text-sm hover:brightness-95 transition">
          Save project
        </button>
      </div>
    {/if}

    {#if projects.length}
      <ul class="space-y-2">
        {#each projects as p (p)}
          <li class="text-sm">
            <div class="flex items-center justify-between gap-2">
              <span class="text-ink font-medium truncate">{p.name}</span>
              <div class="flex items-center gap-2 shrink-0">
                <select
                  value={p.status}
                  onchange={(e: Event) => handleProjectStatusChange(p, (e.target as HTMLSelectElement).value)}
                  class="text-xs font-mono bg-graphite border border-white/10 rounded px-1.5 py-0.5 {statusColor[p.status] || 'text-muted'}"
                >
                  {#each projectStatuses as s (s)}
                    <option value={s}>{s}</option>
                  {/each}
                </select>
                <button onclick={() => handleDeleteProject(p.id)} class="text-muted hover:text-rust transition" aria-label="Delete project">✕</button>
              </div>
            </div>
            <p class="text-muted text-xs mt-0.5">Next: {p.next_step}</p>
          </li>
        {/each}
      </ul>
    {/if}
  </div>

  <!-- Goals -->
  <div>
    <div class="flex items-center justify-between mb-2">
      <p class="text-xs uppercase tracking-wide text-muted font-mono">Goals</p>
      <button
        onclick={() => (showGoalForm = !showGoalForm)}
        class="text-xs text-calm hover:text-ink transition"
      >
        {showGoalForm ? 'Cancel' : '+ Add goal'}
      </button>
    </div>

    {#if showGoalForm}
      <div class="space-y-2 mb-3 bg-graphite rounded p-3 border border-white/10">
        <input bind:value={newGoal.title} placeholder="Goal title"
          class="w-full bg-panel border border-white/10 rounded px-2 py-1.5 text-sm text-ink placeholder:text-muted/60" />
        <input bind:value={newGoal.description} placeholder="Description"
          class="w-full bg-panel border border-white/10 rounded px-2 py-1.5 text-sm text-ink placeholder:text-muted/60" />
        <input bind:value={newGoal.why} placeholder="Why this matters"
          class="w-full bg-panel border border-white/10 rounded px-2 py-1.5 text-sm text-ink placeholder:text-muted/60" />
        <div class="flex items-center gap-2">
          <label class="text-xs text-muted" for="priority">Priority</label>
          <input id="priority" type="number" min="1" max="5" bind:value={newGoal.priority}
            class="w-16 bg-panel border border-white/10 rounded px-2 py-1 text-sm text-ink font-mono" />
        </div>
        <button onclick={handleCreateGoal}
          class="w-full bg-spark text-graphite font-medium rounded py-1.5 text-sm hover:brightness-95 transition">
          Save goal
        </button>
      </div>
    {/if}

    {#if goals.length}
      <ul class="space-y-2">
        {#each goals as g (g)}
          <li class="text-sm">
            <div class="flex items-center justify-between gap-2">
              <span class="text-ink font-medium truncate">{g.title}</span>
              <div class="flex items-center gap-2 shrink-0">
                <select
                  value={g.status}
                  onchange={(e: Event) => handleGoalStatusChange(g, (e.target as HTMLSelectElement).value)}
                  class="text-xs font-mono bg-graphite border border-white/10 rounded px-1.5 py-0.5 {statusColor[g.status] || 'text-muted'}"
                >
                  {#each goalStatuses as s (s)}
                    <option value={s}>{s}</option>
                  {/each}
                </select>
                <button onclick={() => handleDeleteGoal(g.id)} class="text-muted hover:text-rust transition" aria-label="Delete goal">✕</button>
              </div>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>