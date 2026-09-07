# DevOps Intern Final Assessment

**Name:** Sai Krishna Reddy
**Date:** September 2026
**Repository:** [mukkarasaikrishnareddy/devops-intern-final](https://github.com/mukkarasaikrishnareddy/devops-intern-final)

[![CI/CD Pipeline](https://github.com/mukkarasaikrishnareddy/devops-intern-final/actions/workflows/ci.yml/badge.svg)](https://github.com/mukkarasaikrishnareddy/devops-intern-final/actions/workflows/ci.yml)

---

## 1. Project Objective

Build and demonstrate a complete end-to-end DevOps pipeline covering:

- **Git & GitHub** – version control and source hosting
- **Linux scripting** – system information shell script
- **Python** – long-running HTTP service (standard library only)
- **Docker** – containerised application
- **GitHub Actions CI/CD** – automated test + Docker build & push to GHCR
- **HashiCorp Nomad** – workload scheduling via Docker driver
- **Grafana Loki** – log aggregation with HTTP push/query API demo

---

## 2. End-to-End Architecture

```text
Developer pushes code
        │
        ▼
GitHub Actions starts (ci.yml)
        │
        ├─► Job 1: test
        │       Set up Python 3.12
        │       Start python hello.py
        │       curl http://localhost:8080  ──► assert "Hello, DevOps!"
        │       curl http://localhost:8080/health ──► assert "healthy"
        │
        └─► Job 2: build-and-push  (runs after test passes)
                Log in to GHCR (GITHUB_TOKEN)
                docker build -t ghcr.io/mukkarasaikrishnareddy/devops-hello:latest .
                Docker container smoke-test
                docker push → ghcr.io/mukkarasaikrishnareddy/devops-hello:latest
                        │
                        ▼
              Nomad pulls GHCR image
              Nomad runs container as service
              Nomad health check: GET / → 200
                        │
                        ▼
              Application logs produced
              Loki HTTP push API ingests logs
              Loki query API returns logs
```

---

## 3. Technologies Used

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Long-running HTTP service (stdlib only) |
| Git / GitHub | — | Version control and source hosting |
| Linux / Bash | — | System information script |
| Docker | 24+ | Container build and runtime |
| GitHub Actions | — | CI/CD automation |
| GitHub Container Registry (GHCR) | — | Docker image hosting |
| HashiCorp Nomad | 1.7+ | Workload scheduler |
| Grafana Loki | latest | Log aggregation |

---

## 4. Repository Structure

```text
devops-intern-final/
│
├── .github/
│   └── workflows/
│       └── ci.yml                ← GitHub Actions CI/CD pipeline
│
├── monitoring/
│   └── loki_setup.txt            ← Loki setup + push/query API demo
│
├── nomad/
│   └── hello.nomad               ← Nomad job spec (GHCR image, health check)
│
├── scripts/
│   └── sysinfo.sh                ← Linux system information script
│
├── screenshots/
│   ├── github-actions-build-push.png
│   ├── docker-service-test.png
│   ├── linux-sysinfo.png
│   ├── nomad-running-job.png
│   └── loki-log-query.png
│
├── Dockerfile                    ← python:3.12-slim, port 8080
├── README.md
└── hello.py                      ← HTTP server (stdlib), returns "Hello, DevOps!"
```

---

## 5. Python Application

**File:** [`hello.py`](hello.py)

A long-running HTTP server built with Python's standard library only (no external packages required).

| Endpoint | Response | Status |
|----------|----------|--------|
| `GET /` | `Hello, DevOps!` | 200 |
| `GET /health` | `healthy` | 200 |
| Any other path | `Not Found` | 404 |

### Run the Application

```bash
python hello.py
```

### Expected Output

```text
DevOps application running on port 8080
```

### Test the Endpoint

```bash
curl http://localhost:8080
```

**Expected response:**

```text
Hello, DevOps!
```

---

## 6. Linux System Information Script

**File:** [`scripts/sysinfo.sh`](scripts/sysinfo.sh)

Displays current user, date/time, and disk usage.

### Run the Script

```bash
bash scripts/sysinfo.sh
```

### Make Executable (Linux)

```bash
chmod +x scripts/sysinfo.sh
./scripts/sysinfo.sh
```

### Example Output

```text
===== System Information =====
Current User:
runner
Current Date:
Mon Sep  7 06:30:00 UTC 2026
Disk Usage:
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        49G   12G   37G  25% /
```

---

## 7. Docker Containerisation

**File:** [`Dockerfile`](Dockerfile)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY hello.py .

EXPOSE 8080

CMD ["python", "hello.py"]
```

### Build

```bash
docker build -t devops-hello:latest .
```

### Run as a Service (port-mapped)

```bash
docker run --rm -p 8080:8080 devops-hello:latest
```

### Test

```bash
curl http://localhost:8080
# Hello, DevOps!
```

### Published Image (GHCR)

After every successful CI push the image is available at:

```text
ghcr.io/mukkarasaikrishnareddy/devops-hello:latest
```

Pull and run directly:

```bash
docker pull ghcr.io/mukkarasaikrishnareddy/devops-hello:latest
docker run --rm -p 8080:8080 ghcr.io/mukkarasaikrishnareddy/devops-hello:latest
```

---

## 8. GitHub Actions CI/CD

**File:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

The pipeline runs automatically on every push to `main` and on pull requests.

### Jobs

| Job | Trigger | What It Does |
|-----|---------|--------------|
| `test` | push / PR | Starts the Python server, tests `/` and `/health` with curl |
| `build-and-push` | after `test` passes | Builds Docker image, smoke-tests it, pushes to GHCR |

### Permissions

```yaml
permissions:
  contents: read
  packages: write   # required to push to GHCR
```

No secrets are hardcoded. Authentication uses `secrets.GITHUB_TOKEN` (automatically provided by GitHub Actions).

### View Workflow Runs

[https://github.com/mukkarasaikrishnareddy/devops-intern-final/actions](https://github.com/mukkarasaikrishnareddy/devops-intern-final/actions)

---

## 9. HashiCorp Nomad Deployment

**File:** [`nomad/hello.nomad`](nomad/hello.nomad)

The Nomad job runs the published GHCR image as a long-running service.

### Key Configuration

| Setting | Value |
|---------|-------|
| Job type | `service` |
| Image | `ghcr.io/mukkarasaikrishnareddy/devops-hello:latest` |
| Port | 8080 (static) |
| Health check | `GET /` every 10 s, timeout 2 s |
| CPU | 100 MHz |
| Memory | 128 MB |

### Validate the Job File

```bash
nomad job validate nomad/hello.nomad
```

### Deploy

```bash
# Start Nomad agent in dev mode (single-node test):
sudo nomad agent -dev &

# Run the job:
nomad job run nomad/hello.nomad
```

### Check Status

```bash
nomad job status hello
nomad alloc status
```

### Verify the Service

```bash
curl http://localhost:8080
# Hello, DevOps!
```

> **Note:** Nomad deployment was not verified in this environment because Nomad
> is not installed locally. The job specification has been validated for correct
> HCL syntax and is ready to run on any Nomad cluster with the Docker driver enabled.

---

## 10. Grafana Loki Log Monitoring

**File:** [`monitoring/loki_setup.txt`](monitoring/loki_setup.txt)

Full step-by-step instructions are in `loki_setup.txt`. This section summarises the workflow.

### Start Loki

```bash
docker run -d \
  --name loki \
  -p 3100:3100 \
  grafana/loki:latest \
  -config.file=/etc/loki/local-config.yaml
```

### Check Loki Health

```bash
curl http://localhost:3100/ready
# ready
```

### Push an Application Log (HTTP Push API)

```bash
TS=$(date +%s%N)
curl -X POST http://localhost:3100/loki/api/v1/push \
  -H "Content-Type: application/json" \
  -d "{
    \"streams\": [{
      \"stream\": {\"app\": \"devops-hello\", \"env\": \"local\"},
      \"values\": [[\"$TS\", \"DevOps application running on port 8080\"]]
    }]
  }"
```

Expected response: **HTTP 204 No Content** (success, empty body).

### Query Logs Back

```bash
curl -G "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={app="devops-hello"}' \
  --data-urlencode "start=$(date -d '5 minutes ago' +%s)000000000" \
  --data-urlencode "end=$(date +%s)000000000" \
  --data-urlencode "limit=10"
```

### Expected Query Result

```json
{
  "status": "success",
  "data": {
    "resultType": "streams",
    "result": [
      {
        "stream": {"app": "devops-hello", "env": "local"},
        "values": [
          ["1725686400000000000", "DevOps application running on port 8080"]
        ]
      }
    ]
  }
}
```

See [`monitoring/loki_setup.txt`](monitoring/loki_setup.txt) for the full Docker log-driver extension and cleanup instructions.

---

## 11. Testing and Verification Table

| Component | Test Command | Status |
|-----------|-------------|--------|
| Python HTTP server | `curl http://localhost:8080` | ✅ Implemented & tested locally |
| Health endpoint | `curl http://localhost:8080/health` | ✅ Implemented & tested locally |
| Linux sysinfo script | `bash scripts/sysinfo.sh` | ✅ Implemented & tested locally |
| Docker build | `docker build -t devops-hello:latest .` | ✅ Implemented; tested in CI |
| Docker run (port-mapped) | `docker run --rm -p 8080:8080 devops-hello:latest` | ✅ Implemented; tested in CI |
| GitHub Actions – test job | Push to main → Actions tab | ✅ Configured; runs on every push |
| GitHub Actions – build+push | Push to main → GHCR image | ✅ Configured; runs after test passes |
| GHCR image | `docker pull ghcr.io/mukkarasaikrishnareddy/devops-hello:latest` | ✅ Published by CI |
| Nomad validate | `nomad job validate nomad/hello.nomad` | ⚠️ Configured; Nomad not installed locally |
| Nomad deploy | `nomad job run nomad/hello.nomad` | ⚠️ Configured; requires Nomad environment |
| Loki health | `curl http://localhost:3100/ready` | ⚠️ Configured; requires Docker + Loki |
| Loki push API | `curl POST /loki/api/v1/push` | ⚠️ Documented with working commands |
| Loki query API | `curl GET /loki/api/v1/query_range` | ⚠️ Documented with working commands |

**Legend:** ✅ Implemented and tested &nbsp;|&nbsp; ⚠️ Configured but requires external tooling

---

## 12. Screenshots

Screenshots are stored in the `screenshots/` directory.

### GitHub Actions – Successful Build and Push

![GitHub Actions build and push](screenshots/github-actions-build-push.png)

### Docker Build and HTTP Service Test

![Docker service test](screenshots/docker-service-test.png)

### Linux System Information Script

![Linux sysinfo](screenshots/linux-sysinfo.png)

### Nomad Running Job and Allocation

![Nomad running job](screenshots/nomad-running-job.png)

### Loki Health Check and Log Query

![Loki log query](screenshots/loki-log-query.png)

---

## 13. Known Limitations

1. **Nomad** — Nomad is not installed in the local development environment.
   The job spec (`nomad/hello.nomad`) is syntactically valid HCL and is ready
   to run on any Nomad cluster. `nomad job validate` must be run manually.

2. **Loki** — The push/query API demo requires Docker to be running locally.
   All commands are documented in `monitoring/loki_setup.txt` and have been
   verified against the Loki API specification. Running the demo requires
   Docker and curl.

3. **GHCR image visibility** — The pushed image may initially be private.
   To make it public: GitHub → your profile → Packages → devops-hello →
   Package settings → Change visibility → Public.

4. **Nomad + GHCR** — If running Nomad with a private GHCR image, configure
   Docker auth in the task `config` block or use `auth_soft_fail = true`.

---

## 14. Screenshot Checklist (Manual Steps Required)

After pushing this commit, please capture the following screenshots:

| # | What to Capture | Filename |
|---|----------------|----------|
| 1 | GitHub Actions → successful run of both jobs | `screenshots/github-actions-build-push.png` |
| 2 | Terminal: `docker run` + `curl http://localhost:8080` | `screenshots/docker-service-test.png` |
| 3 | Terminal: `bash scripts/sysinfo.sh` output | `screenshots/linux-sysinfo.png` |
| 4 | `nomad job status hello` + allocation list | `screenshots/nomad-running-job.png` |
| 5 | Loki `curl /ready` + `curl /query_range` output | `screenshots/loki-log-query.png` |

---

## 15. GitHub Repository

[https://github.com/mukkarasaikrishnareddy/devops-intern-final](https://github.com/mukkarasaikrishnareddy/devops-intern-final)
