<script lang="ts">
	import { createCheckIn } from '$lib/models/api';

  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  let didPlannedTask: boolean | null = $state(null); // null until chosen, avoids defaulting to "yes"
  let motivationLevel = $state(5);
  let socialMediaCount = $state(0);
  let reinstalledApp = $state(false);
  let triggerNote = $state('');
  let submitting = $state(false);
  let submitted = $state(false);
  let error: string | null = $state(null);

  async function handleSubmit() {
    if (didPlannedTask === null) {
      error = 'Choose whether you did your planned task.';
      return;
    }
    error = null;
    submitting = true;
    try {
      await createCheckIn({
        date: new Date().toISOString().slice(0, 10),
        did_planned_task: didPlannedTask,
        motivation_level: motivationLevel,
        social_media_opened_count: socialMediaCount,
        reinstalled_app: reinstalledApp,
        trigger_note: triggerNote || null,
      });
      submitted = true;
      dispatch('saved');
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (e: any) {
      error = e.message;
    } finally {
      submitting = false;
    }
  }
</script>

<div class="bg-panel rounded-lg p-5 border border-white/5">
  <h2 class="font-display text-lg text-ink mb-4">Today's check-in</h2>

  {#if submitted}
    <p class="text-calm text-sm">Saved. See you tomorrow.</p>
  {:else}
    <div class="space-y-4">
      <div>
        <p class="text-sm text-muted mb-2">Did you do your planned task?</p>
        <div class="flex gap-2">
          <button
            type="button"
            class="px-3 py-1.5 rounded text-sm border transition-colors {didPlannedTask === true ? 'bg-spark text-graphite border-spark' : 'border-white/10 text-ink hover:border-white/30'}"
            onclick={() => (didPlannedTask = true)}>Yes</button>
          <button
            type="button"
            class="px-3 py-1.5 rounded text-sm border transition-colors {didPlannedTask === false ? 'bg-rust text-ink border-rust' : 'border-white/10 text-ink hover:border-white/30'}"
            onclick={() => (didPlannedTask = false)}>No</button>
        </div>
      </div>

      <div>
        <label class="text-sm text-muted mb-1 block" for="motivation">
          Motivation level: <span class="font-mono text-ink">{motivationLevel}/10</span>
        </label>
        <input id="motivation" type="range" min="1" max="10" bind:value={motivationLevel} class="w-full accent-spark" />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="text-sm text-muted mb-1 block" for="social">Times you opened social media</label>
          <input id="social" type="number" min="0" bind:value={socialMediaCount}
            class="w-full bg-graphite border border-white/10 rounded px-2 py-1.5 text-sm text-ink font-mono" />
        </div>
        <div class="flex items-end pb-1.5">
          <label class="flex items-center gap-2 text-sm text-muted">
            <input type="checkbox" bind:checked={reinstalledApp} class="accent-rust" />
            Reinstalled an app today
          </label>
        </div>
      </div>

      <div>
        <label class="text-sm text-muted mb-1 block" for="trigger">What triggered it (optional)</label>
        <input id="trigger" type="text" bind:value={triggerNote} placeholder="bored, avoiding a task, after finishing something..."
          class="w-full bg-graphite border border-white/10 rounded px-2 py-1.5 text-sm text-ink placeholder:text-muted/60" />
      </div>

      {#if error}
        <p class="text-rust text-sm">{error}</p>
      {/if}

      <button
        onclick={handleSubmit}
        disabled={submitting}
        class="w-full bg-spark text-graphite font-medium rounded py-2 text-sm disabled:opacity-50 hover:brightness-95 transition"
      >
        {submitting ? 'Saving...' : 'Save check-in'}
      </button>
    </div>
  {/if}
</div>