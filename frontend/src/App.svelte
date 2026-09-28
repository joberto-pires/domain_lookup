<script>
  import { onMount } from "svelte";
  import { submitJob, getJob, listJobs, setReview } from "./lib/api.js";
  import { pollJob } from "./lib/polling.js";

  let domain = "";
  let currentJob = null;
  let jobs = [];
  let selectedJob = null;
  let filter = "all";
  let stopPolling = null;

  onMount(refreshHistory);

  async function refreshHistory() {
    jobs = await listJobs();
  }

  async function handleSubmit() {
    const result = await submitJob(domain);
    currentJob = result;
    startPolling(result.job_id);
  }

  function startPolling(id) {
    if (stopPolling) stopPolling();
    stopPolling = pollJob(
      id,
      (data) => (currentJob = data),
      (data) => {
        currentJob = data;
        refreshHistory();
      }
    );
  }

  async function selectJob(job) {
    selectedJob = await getJob(job.id);
    filter = "all";
  }

  async function toggleReview(hostname, current) {
    await setReview(selectedJob.domain, hostname, !current);
    selectedJob = await getJob(selectedJob.id);
  }

  function filteredHostnames() {
    if (!selectedJob) return [];
    if (filter === "all") return selectedJob.results || [];
    return (selectedJob.changes && selectedJob.changes[filter]) || [];
  }
</script>

<h1>Domain Lookup</h1>

<section>
  <input bind:value={domain} placeholder="example.com" />
  <button on:click={handleSubmit}>Submit</button>
</section>

{#if currentJob && currentJob.status}
  <section>
    <h2>Current Job: {currentJob.id || currentJob.job_id}</h2>
    <p>Status: {currentJob.status} | Attempts: {currentJob.attempts}</p>
    {#if currentJob.error}<p>Error: {currentJob.error}</p>{/if}
  </section>
{/if}

<section>
  <h2>History</h2>
  {#each jobs as job}
    <button on:click={() => selectJob(job)}>
      {job.domain} — {job.status} ({job.result_count ?? 0} hosts)
    </button>
  {/each}
</section>

{#if selectedJob}
  <section>
    <h2>Job Detail: {selectedJob.id}</h2>
    <p>Domain: {selectedJob.domain}</p>
    <p>Status: {selectedJob.status}</p>
    <p>Baseline: {selectedJob.previous_success_job_id || "none (first run)"}</p>
    <p>
      Added: {selectedJob.added_count ?? "—"} |
      Removed: {selectedJob.removed_count ?? "—"} |
      Unchanged: {selectedJob.unchanged_count ?? "—"}
    </p>

    <div>
      <button on:click={() => (filter = "all")}>All</button>
      <button on:click={() => (filter = "added")}>Added</button>
      <button on:click={() => (filter = "removed")}>No longer observed</button>
      <button on:click={() => (filter = "unchanged")}>Unchanged</button>
    </div>

    <ul>
      {#each filteredHostnames() as host}
        <li>
          <input
            type="checkbox"
            checked={host.reviewed}
            on:change={() => toggleReview(host.hostname, host.reviewed)}
          />
          {host.hostname}
        </li>
      {/each}
    </ul>
  </section>
{/if}
