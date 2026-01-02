# Systemd Services Documentation

This document explains the systemd services configured for the Nuze backend infrastructure.

## Overview

Systemd is Linux's service manager that handles starting, stopping, and managing background services. We use it to ensure Nuze containers start automatically after system reboots.

## Configured Services

### `nuze-gpu-check.service`

**Location:** `/etc/systemd/system/nuze-gpu-check.service`

**Purpose:** Ensures Docker containers start cleanly after boot, with GPU drivers ready.

```ini
[Unit]
Description=Nuze GPU Check and Container Restart
After=docker.service nvidia-persistenced.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'sleep 30 && cd /home/linuxu/Desktop/nuze-backend && docker compose down && docker compose up -d'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

### How It Works

| Directive | Purpose |
|-----------|---------|
| `After=docker.service nvidia-persistenced.service` | Wait for Docker and GPU drivers |
| `Requires=docker.service` | Fail if Docker isn't available |
| `Type=oneshot` | Run once, not continuously |
| `sleep 30` | Allow GPU to fully initialize |
| `docker compose down` | Clean shutdown of any running containers |
| `docker compose up -d` | Start fresh containers |
| `RemainAfterExit=yes` | Keep service marked as "active" after completion |

## Common Commands

```bash
# Check service status
systemctl status nuze-gpu-check.service

# Enable service at boot
sudo systemctl enable nuze-gpu-check.service

# Disable service
sudo systemctl disable nuze-gpu-check.service

# Manually run the service
sudo systemctl start nuze-gpu-check.service

# View logs
journalctl -u nuze-gpu-check.service

# Reload after editing service file
sudo systemctl daemon-reload
```

## Interaction with Docker Restart Policy

The containers also have `restart: unless-stopped` in `docker-compose.yml`. Both work together:

| Scenario | Behavior |
|----------|----------|
| **System boot** | Systemd service runs, cleanly restarts all containers |
| **Docker restart** | Containers auto-restart via restart policy |
| **Manual `docker compose down`** | Containers stay down until manually started |

## Troubleshooting

**Containers not starting after reboot:**
```bash
# Check if service ran
systemctl status nuze-gpu-check.service

# Check service logs
journalctl -u nuze-gpu-check.service -b

# Check Docker status
systemctl status docker
```

**GPU not available:**
```bash
# Verify GPU is detected
nvidia-smi

# Check nvidia-persistenced
systemctl status nvidia-persistenced
```
