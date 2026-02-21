# presentation/handlers

Handlers/controllers.

Put here:
- functions that coordinate one or more domain services
- mapping domain results to presentation DTOs

Rules:
- no direct HTTP logic besides preparing a response object
- no raw DAL calls (handlers call services).
