<script lang="ts">
	import { onMount } from 'svelte';
	import { PUBLIC_API_URL } from '$env/static/public';

	// $state is Svelte 5's reactive declaration - when this changes, the DOM updates.
	let status = $state('checking...');

	onMount(async () => {
		try {
			const res = await fetch(`${PUBLIC_API_URL}/health`);
			const data = await res.json();
			status = data.status;
		} catch (err) {
			status = `unreachable: ${err instanceof Error ? err.message : String(err)}`;
		}
	});
</script>

<main class="mx-auto max-w-xl p-12 font-sans">
	<h1 class="text-3xl font-bold">BoosterTutor</h1>
	<p class="mt-4 text-slate-600">
		API status:
		<span class="font-mono font-semibold">{status}</span>
	</p>
</main>
