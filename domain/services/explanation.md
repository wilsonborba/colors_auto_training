# domain/services

Domain services = use-cases that orchestrate adapters.

Examples:
- `video_queue_service.py`: enqueue, reprioritize, retry policies
- `download_service.py`: call youtube_adapter + filesystem adapter + sqlite adapter
- `dex_service.py`: frame sampling → detection → ROI → mask, using adapters

Rules:
- services may call multiple adapters
- services must be testable (inject adapters)
- services do not contain HTTP / UI concerns
