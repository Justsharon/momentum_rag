<script lang="ts">
	import { ask, submitFeedback } from '$lib/models/api';

	type Source = {
		source_type: string;
		title: string;
	};

	let question: string = $state('');
	let answer: string | null = $state(null);
	let sources: Source[] = $state([]);
  let logId: string | null = $state(null);
  let feedbackGiven: number | null = $state(null);
	let loading: boolean = $state(false);
	let error: string | null = $state(null);

	const suggestions = [
		'What should I focus on today?',
		'What usually happens after I finish a big goal?',
		'What tends to come right before I reinstall social media?'
	];

	async function handleAsk() {
		if (!question.trim()) return;
		loading = true;
		error = null;
		answer = null;
    feedbackGiven = null;
		try {
			const res = await ask(question);
			answer = res.answer;
			sources = res.sources;
      logId = res.log_id;
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	function useSuggestion(s: string) {
		question = s;
		handleAsk();
	}

 
  async function giveFeedback(value: number) {
    if (!logId || feedbackGiven) return;
    feedbackGiven = value;
    try {
      await submitFeedback(logId, value);
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  }
</script>

<div class="bg-panel rounded-lg border border-white/5 p-5">
	<h2 class="font-display text-ink mb-4 text-lg">Ask your history</h2>

	<div class="mb-3 flex gap-2">
		<input
			type="text"
			bind:value={question}
			onkeydown={(e) => e.key === 'Enter' && handleAsk()}
			placeholder="What should I work on next?"
			class="bg-graphite text-ink placeholder:text-muted/60 flex-1 rounded border border-white/10 px-3 py-2 text-sm"
		/>
		<button
			onclick={handleAsk}
			disabled={loading}
			class="bg-calm text-graphite rounded px-4 py-2 text-sm font-medium transition hover:brightness-95 disabled:opacity-50"
		>
			{loading ? '...' : 'Ask'}
		</button>
	</div>

	<div class="mb-4 flex flex-wrap gap-2">
		{#each suggestions as s (s)}
			<button
				onclick={() => useSuggestion(s)}
				class="text-muted hover:text-ink rounded-full border border-white/10 px-3 py-1 text-xs transition hover:border-white/30"
			>
				{s}
			</button>
		{/each}
	</div>

	{#if error}
		<p class="text-rust text-sm">{error}</p>
	{/if}

	{#if answer}
		<div class="border-t border-white/5 pt-4">
			<p class="text-ink text-sm leading-relaxed whitespace-pre-wrap">{answer}</p>
			{#if sources.length}
				<div class="mt-3 flex flex-wrap gap-1.5">
					{#each sources as s (s)}
						<span
							class="text-muted bg-graphite rounded border border-white/10 px-2 py-0.5 font-mono text-xs"
						>
							{s.source_type}: {s.title}
						</span>
					{/each}
				</div>
			{/if}

      <div class="mt-3 flex items-center gap-2">
        <span class="text-xs text-muted">Helpful?</span>
        <button
          onclick={() => giveFeedback(1)}
          disabled={feedbackGiven !== null}
          class="text-sm px-2 py-0.5 rounded border transition-colors {feedbackGiven === 1 ? 'border-calm text-calm' : 'border-white/10 text-muted hover:border-white/30'} disabled:cursor-default"
          aria-label="Thumbs up"
        >
          👍
        </button>
        <button
          onclick={() => giveFeedback(-1)}
          disabled={feedbackGiven !== null}
          class="text-sm px-2 py-0.5 rounded border transition-colors {feedbackGiven === -1 ? 'border-rust text-rust' : 'border-white/10 text-muted hover:border-white/30'} disabled:cursor-default"
          aria-label="Thumbs down"
        >
          👎
        </button>
        {#if feedbackGiven !== null}
          <span class="text-xs text-muted">Thanks, saved.</span>
        {/if}
      </div>
		</div>
	{/if}
</div>
