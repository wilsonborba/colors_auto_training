# presentation

Presentation layer = API routes, handlers/controllers, and SSR/static frontend.

Put here:
- FastAPI app setup, routers
- handlers that call domain services
- response DTOs (your standard {status_code, message, data})
- SSR pages/templates and their JS/CSS separated by feature

Rules:
- routes should be thin: validate input → call handler → map to HTTP status
- handlers may call multiple services
- no DAL usage directly from routes (routes → handlers → services → adapters).
