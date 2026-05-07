---
name: Use docker compose up -d without --build flag
description: User doesn't want --build flag on docker compose up as it re-downloads everything — only use it when explicitly needed
type: feedback
originSessionId: 4ce7ef12-5c8d-417e-bc2e-f3f0a76f93a5
---
Don't use `docker compose build` or `docker compose up -d --build` when source files are volume-mounted. Check `docker-compose.yml` volumes first — if the service mounts `./backend:/app`, a `docker compose restart <service>` is all that's needed. Only build when the Dockerfile itself changes (new deps, base image, etc.).

**Why:** Full image rebuilds trigger apt-get and pip installs — many minutes of unnecessary downloads. backend and worker both mount `./backend:/app`, so Python source changes are picked up on restart with no rebuild at all.

**How to apply:** After editing Python files, run `docker compose restart worker` (or `backend`). Only run `docker compose build` if requirements.txt or the Dockerfile changed. Never run it for `.py` file changes.
