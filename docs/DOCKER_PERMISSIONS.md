# Docker Permission Issues

## Frontend `.next` Directory Permissions

### Problem

When running `docker compose up`, the frontend container may fail with:

```
Error: EACCES: permission denied, unlink '/app/.next/server/app-paths-manifest.json'
```

### Root Cause

Docker containers run as `root` by default. When Next.js creates the `.next` build directory, it's owned by root. The development server then can't delete/modify these files.

### Solution

**1. Fix docker-compose.yml** (Permanent):

```yaml
frontend:
  user: "${UID:-1000}:${GID:-1000}" # Run as your user, not root
```

**2. Clean existing root-owned files** (One-time):

```bash
# Stop frontend
docker compose stop frontend

# Remove root-owned .next directory
sudo rm -rf frontend/.next

# Or if that doesn't work (nested permissions):
sudo find frontend/.next -type f -exec chmod 666 {} \;
sudo find frontend/.next -type d -exec chmod 777 {} \;
rm -rf frontend/.next

# Restart
docker compose up -d frontend
```

### Prevention

The `user: "${UID:-1000}:${GID:-1000}"` setting in docker-compose.yml ensures:

- Container runs as your user ID
- Files created have your ownership
- No permission conflicts

### Verification

After fixing, verify ownership:

```bash
ls -la frontend/.next
# Should show your username, not root
```

### Alternative: Named Volume

If user mapping doesn't work, use a named volume:

```yaml
frontend:
  volumes:
    - ./frontend:/app
    - /app/node_modules
    - frontend_cache:/app/.next # ← Separate volume for .next

volumes:
  frontend_cache:
```

## Backend Volumes

**Important**: Don't delete backend volumes! They contain:

- `node_modules` (large npm packages)
- Python packages (pip installs)
- Database data

Only clean frontend `.next` directory as needed.
