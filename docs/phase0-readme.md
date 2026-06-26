@'
# Phase 0 — Repo & Infra Setup

## What Was Built
- Full project folder skeleton with all Python packages initialized
- `.gitignore` covering Python, Node, MLflow, Redis, and OS artifacts
- `.env.example` with all environment variables for every service
- `requirements.txt` — all production dependencies pinned with versions
- `requirements-dev.txt` — adds pytest, black, ruff on top of production deps
- Python virtual environment (`venv`) with all packages installed
- Redis verified running at `localhost:6379`
- Apache Kafka extracted to `D:\kafka`, ZooKeeper and broker startup scripts created
- Java (Temurin 21 LTS) installed and added to PATH
- Kafka topics created: `raw-events`, `computed-features` (3 partitions each)
- PowerShell scripts for all infra ops — no Git Bash, no Docker required
- `infra/verify-infra.ps1` confirms all services healthy in one command

## How to Start Services
- ZooKeeper: run `.\infra\start-zookeeper.ps1` in its own terminal
- Kafka: run `.\infra\start-kafka.ps1` in its own terminal
- Topics: run `.\infra\create-topics.ps1` once after Kafka is up
- Verify: run `.\infra\verify-infra.ps1`

## Key Decisions
- PowerShell `.ps1` scripts instead of `.sh` — works natively on Windows without Git Bash
- Kafka runs as a local binary process, not a service — keeps things visible and controllable
- Redis installed as a Windows service — auto-starts with the machine
- All dependencies pinned to exact versions — reproducible installs across machines

## Files Created This Phase
- `.gitignore`
- `.env.example`
- `.env`
- `requirements.txt`
- `requirements-dev.txt`
- `infra/start-zookeeper.ps1`
- `infra/start-kafka.ps1`
- `infra/create-topics.ps1`
- `infra/verify-infra.ps1`
- All `feature_store/`, `consumer/`, `scheduler/`, `tests/` `__init__.py` files
- `data/raw/.gitkeep`, `data/snapshots/.gitkeep`, `models/artifacts/.gitkeep`
'@ | Set-Content -Path "docs/phase0-readme.md" -Encoding UTF8

Write-Host "Phase 0 README created."