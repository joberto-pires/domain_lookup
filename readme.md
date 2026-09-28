# Domain Lookup Service

## Startup
```bash
docker compose up --build
docker compose exec api alembic upgrade head
http://localhost:5173
http://localhost:8000/docs
```

## Architecture
- **API**: Normalizes domain, creates job, publishes Celery task, returns 202.
- **Worker**: Fetches from provider, normalizes hostnames, computes changes, stores snapshot.
- **Concurrency**: Partial unique index on `jobs(domain)` where status is active.
- **Consistency**: Success commit is a single transaction (job, results, changes, baseline).
- **Review state**: Stored separately by `(domain, hostname)`, preserved across lookups.

## Time Spent
Approximately 8–10 hours.

## Known Limitations
- Broker publish is not transactional with DB. If publish fails after commit, job may remain `queued`.
- Worker crash can leave a job stuck in `running`. No recovery reaper.
- No authentication, scheduled monitoring, or active scanning.
- Mock mode uses Redis counter; not intended for production.
