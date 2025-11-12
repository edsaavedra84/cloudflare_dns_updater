# Docker Deployment for DNS Updater

This folder contains Docker configuration files to run the DNS updater in a container.

## Quick Start

1. **Create configuration file** (from project root):
   ```bash
   mkdir -p config
   cp config.sample.json config/config.json
   # Edit config/config.json with your Cloudflare credentials
   ```

2. **Run with Docker Compose**:
   ```bash
   cd docker
   docker-compose up -d
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f dns-updater
   ```

## Files

- **Dockerfile**: Container image definition
- **docker-compose.yml**: Service orchestration configuration

## Configuration

The container expects:
- Configuration file at: `../config/config.json` (mounted read-only)
- Logs directory at: `../logs/` (mounted read-write)

## Environment Variables

You can customize the timezone by editing `docker-compose.yml`:
```yaml
environment:
  - TZ=America/New_York  # Change to your timezone
```

## Resource Limits

Default limits are set in `docker-compose.yml`:
- CPU: 0.5 cores max, 0.1 cores reserved
- Memory: 256MB max, 64MB reserved

Adjust these based on your needs.

## Troubleshooting

**Container won't start:**
- Ensure `config/config.json` exists and is valid
- Check logs: `docker-compose logs dns-updater`

**DNS not updating:**
- Verify Cloudflare credentials in config file
- Check logs for API errors
- Ensure container has network access

**View container status:**
```bash
docker-compose ps
```

**Stop container:**
```bash
docker-compose down
```

**Rebuild after code changes:**
```bash
docker-compose up -d --build
```
