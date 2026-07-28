<script lang="ts">
	// @ts-expect-error CSS import
	import '../app.css';

	let { children } = $props();
</script>


{@render children()}
