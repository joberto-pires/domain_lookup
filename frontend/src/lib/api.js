const BASE = "http://localhost:8000";

export async function submitJob(domain) {
  const res = await fetch(`${BASE}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain }),
  });
  return res.json();
}

export async function getJob(id) {
  const res = await fetch(`${BASE}/jobs/${id}`);
  return res.json();
}

export async function listJobs(domain) {
  const q = domain ? `?domain=${encodeURIComponent(domain)}` : "";
  const res = await fetch(`${BASE}/jobs${q}`);
  return res.json();
}

export async function setReview(domain, hostname, reviewed) {
  const res = await fetch(
    `${BASE}/domains/${domain}/hostnames/${hostname}/review`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reviewed }),
    }
  );
  return res.json();
}
