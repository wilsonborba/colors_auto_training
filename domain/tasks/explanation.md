# domain/tasks

Task runners / scheduled jobs.

Put here:
- periodic download worker
- pipeline stage workers (detect, crop, mask, label, train, evaluate)
- retry loops and job state transitions (but not UI)

Rules:
- tasks call domain services
- tasks are the bridge between 'daemon/worker world' and services
