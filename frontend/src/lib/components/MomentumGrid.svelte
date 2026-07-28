<script lang="ts">
	import { SvelteDate } from "svelte/reactivity";

  type Checkin = {
    date: string;
    motivation_level?: number;
    reinstalled_app?: boolean;
    did_planned_task?: boolean;
  };

  const { checkins = [] }: { checkins?: Checkin[] } = $props();

  const DAYS = 84;

  function buildCells() {
    const byDate = new Map(checkins.map((c) => [c.date, c]));
    const cells = [];
    const today = new Date();
    for (let i = DAYS - 1; i >= 0; i--) {
      const d = new SvelteDate(today);
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      cells.push({ date: key, entry: byDate.get(key) });
    }
    return cells;
  }

  let cells = $derived(buildCells());

  function intensity(entry: Checkin | undefined): string {
    if (!entry) return 'bg-panel border border-white/5';
    const level: number = entry.motivation_level ?? 0;
    const buckets = [
      'bg-[#3A342A]',
      'bg-[#5A4C30]',
      'bg-[#8A6E35]',
      'bg-[#C1943F]',
      'bg-spark',
    ];
    const idx = Math.min(4, Math.max(0, Math.floor((level - 1) / 2)));
    return buckets[idx];
  }
</script>

<div>
  <div class="flex items-baseline justify-between mb-3">
    <h2 class="font-display text-lg text-ink">Momentum, last 12 weeks</h2>
    <div class="flex items-center gap-3 text-xs text-muted font-mono">
      <span class="flex items-center gap-1">
        <span class="w-2.5 h-2.5 rounded-sm bg-spark inline-block"></span> high motivation
      </span>
      <span class="flex items-center gap-1">
        <span class="w-2.5 h-2.5 rounded-sm bg-rust inline-block"></span> reinstalled
      </span>
    </div>
  </div>

  <div
    class="grid grid-flow-col gap-1 overflow-x-auto pb-2"
    style="grid-template-rows: repeat(7, minmax(0, 1fr));"
  >
    {#each cells as cell (cell.date)}
      <div
        class="w-3 h-3 rounded-sm relative group {intensity(cell.entry)}"
        title={cell.date}
      >
        {#if cell.entry?.reinstalled_app}
          <span class="absolute inset-0 rounded-sm ring-2 ring-rust"></span>
        {/if}
      </div>
    {/each}
  </div>
</div>