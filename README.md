# DevOps Intern Final Assessment

**Author:** Sai Krishna Reddy
**Repository:** [https://github.com/mukkarasaikrishnareddy/devops-intern-final](https://github.com/mukkarasaikrishnareddy/devops-intern-final)

---

## 1. Project Overview

This repository implements a complete DevOps automation pipeline for a long-running Python HTTP application. It demonstrates modern DevOps practices including containerisation, CI/CD automation with GitHub Container Registry (GHCR), workload scheduling with Nomad, structured log ingestion and querying with Grafana Loki, and system diagnostic scripting in Linux.

---

## 2. CI/CD & Deployment Pipeline

```text
Developer pushes code
        ↓
GitHub Actions runs Python tests
        ↓
Docker image is built
        ↓
Docker image is pushed to GHCR
        ↓
Nomad pulls and runs the image
        ↓
Application exposes port 8080
        ↓
Application generates logs
        ↓
Logs are sent to Loki
        ↓
Logs are queried from Loki
```

---

## 3. Technologies Used

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.14.4 (Windows) / 3.12.3 (WSL) | Standard-library HTTP web service |
| **Git** | 2.53.0.windows.1 | Source control and version tracking |
| **Docker Desktop** | 27.5.1 | Container build & local runtime |
| **Docker Compose** | v2.32.4-desktop.1 | Multi-container management |
| **GitHub Actions** | v4 / v5 actions | CI/CD automation & GHCR publishing |
| **GHCR** | — | Container image registry (`ghcr.io/mukkarasaikrishnareddy/devops-hello:latest`) |
| **HashiCorp Nomad** | 2.0.5 | Container workload orchestration |
| **Grafana Loki** | 3.7.7 | Structured log aggregation & querying |
| **Linux / WSL2** | Ubuntu (WSL2) | System information scripting environment |

---

## 4. Repository Structure

```text
devops-intern-final/
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions workflow (test, build, push to GHCR)
├── monitoring/
│   ├── loki_setup.txt            # Loki setup guide & push/query API instructions
│   └── send_logs.py              # Python stdlib script pushing & querying Loki logs
├── nomad/
│   └── hello.nomad               # Nomad job spec (service, health check, resource limits)
├── screenshots/
│   ├── docker-build-run.png      # Verified Docker build & execution screenshot
│   ├── github-actions-success.png# Verified GitHub Actions workflow screenshot
│   └── linux-sysinfo.png         # Verified Linux sysinfo script screenshot
├── scripts/
│   └── sysinfo.sh                # Linux system information script (LF endings)
├── Dockerfile                    # Container definition (python:3.12-slim)
├── hello.py                      # Long-running HTTP service (0.0.0.0:8080)
└── README.md                     # Project documentation
```

---

## 5. Application Behavior (`hello.py`)

The application is a long-running HTTP service built exclusively using Python's standard-library `http.server` module.

- **Host:** `0.0.0.0`
- **Port:** `8080` (overridable via `PORT` environment variable)

### Endpoints
- `GET /` → Returns `200 OK` with body `Hello, DevOps!`
- `GET /health` → Returns `200 OK` with body `healthy`
- Any other path → Returns `404 Not Found` with body `Not Found`

### Local Execution & Testing

Start the application:
```bash
python hello.py
```

Test HTTP responses:
```bash
curl http://localhost:8080
curl http://localhost:8080/health
curl -v http://localhost:8080/unknown
```

---

## 6. Docker Containerisation (`Dockerfile`)

### Dockerfile Specification
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY hello.py .

EXPOSE 8080

CMD ["python", "hello.py"]
```

### Build & Smoke Test
```bash
# Build image
docker build -t devops-hello:latest .

# Run container
docker run -d --name devops-hello-container -p 18080:8080 devops-hello:latest

# Verify endpoints
curl http://localhost:18080
curl http://localhost:18080/health

# Inspect logs
docker logs devops-hello-container

# Clean up
docker rm -f devops-hello-container
```

---

## 7. GitHub Actions CI/CD (`.github/workflows/ci.yml`)

The workflow triggers on `push` and `pull_request` to the `main` branch.

### Key Features
1. **Permissions:** Explicitly set to `contents: read` and `packages: write`.
2. **Job 1 (`test`):**
   - Sets up Python 3.12.
   - Compiles `hello.py` syntax.
   - Starts `hello.py` in the background and tests `/` and `/health`.
   - Uploads `server.log` artifact on completion or failure (`actions/upload-artifact@v4`).
3. **Job 2 (`build-and-push`):**
   - Depends on `test` passing (`needs: test`).
   - Authenticates to GHCR using `${{ secrets.GITHUB_TOKEN }}`.
   - Lowercases image tag: `ghcr.io/mukkarasaikrishnareddy/devops-hello:latest`.
   - Builds Docker image and performs container smoke test before pushing.
   - Pushes image to GHCR and verifies image digest.

---

## 8. GHCR Package Settings

The container image is published to:
```text
ghcr.io/mukkarasaikrishnareddy/devops-hello:latest
```

### Making the GHCR Package Public
1. Navigate to GitHub → Profile / Organization → **Packages**.
2. Select `devops-hello` package.
3. Click **Package settings** → **Change package visibility**.
4. Set visibility to **Public** and confirm.

---

## 9. Nomad Orchestration (`nomad/hello.nomad`)

### Job Definition
```hcl
job "hello" {
  datacenters = ["dc1"]
  type        = "service"

  group "hello" {
    count = 1

    network {
      port "http" {
        to = 8080
      }
    }

    service {
      name     = "hello"
      port     = "http"
      provider = "nomad"
      tags     = ["devops", "http"]

      check {
        name     = "http-health"
        type     = "http"
        path     = "/health"
        interval = "10s"
        timeout  = "2s"
      }
    }

    task "hello" {
      driver = "docker"

      config {
        image = "ghcr.io/mukkarasaikrishnareddy/devops-hello:latest"
        ports = ["http"]
      }

      resources {
        cpu    = 100
        memory = 128
      }
    }
  }
}
```

### Execution Commands
```bash
# Validate HCL syntax
nomad job validate nomad/hello.nomad

# Run job on running agent
nomad job run nomad/hello.nomad

# Check job & allocation status
nomad job status hello
nomad alloc status
```

### Nomad Execution Note

The Nomad job specification was validated successfully using:

```bash
nomad job validate nomad/hello.nomad
```

The job uses a Linux Docker image hosted on GHCR (`ghcr.io/mukkarasaikrishnareddy/devops-hello:latest`). On the native Windows Nomad agent, the Docker driver reported that Docker was configured for Linux containers and requested Windows containers (`Docker is configured with Linux containers; switch to Windows Containers`). Therefore, the job was not claimed as successfully deployed on the native Windows agent. The job specification is syntactically valid HCL and is intended to run in a Linux or WSL2-based Nomad environment.

---

## 10. Loki Log Aggregation (`monitoring/send_logs.py`)

### Setup & Ingestion Steps
1. Start Grafana Loki container:
   ```bash
   docker run -d --name loki -p 3100:3100 grafana/loki:latest "-config.file=/etc/loki/local-config.yaml"
   ```
2. Verify readiness endpoint:
   ```bash
   curl http://localhost:3100/ready
   ```
3. Push logs via Python standard-library script:
   ```bash
   python monitoring/send_logs.py
   ```
   *Sends JSON log payload to `http://localhost:3100/loki/api/v1/push` with label `job=devops-hello` (returns HTTP 204).*
4. Query Loki log entries:
   ```bash
   curl "http://localhost:3100/loki/api/v1/query_range?query=%7Bjob%3D%22devops-hello%22%7D"
   ```

---

## 11. Linux System Information Script (`scripts/sysinfo.sh`)

The script outputs user context, current UTC timestamp, and disk filesystem usage.

```bash
# Execute in Linux or WSL
bash scripts/sysinfo.sh
```

---

## 12. Verification & Testing Summary

| Test Case | Command | Result / Status |
|-----------|---------|-----------------|
| Python `hello.py` GET `/` | `curl http://localhost:8081` | ✅ Passed (`Hello, DevOps!`) |
| Python `hello.py` GET `/health` | `curl http://localhost:8081/health` | ✅ Passed (`healthy`) |
| Python `hello.py` GET 404 path | `curl http://localhost:8081/unknown` | ✅ Passed (`404 Not Found`) |
| Docker image build | `docker build -t devops-hello:latest .` | ✅ Passed |
| Docker container smoke test | `docker run -p 18080:8080 ...` | ✅ Passed |
| GitHub Actions workflow syntax | `python -m py_compile / yaml validate` | ✅ Passed |
| Nomad HCL syntax | `nomad job validate nomad/hello.nomad` | ✅ Passed (`Job validation successful`) |
| Nomad job submission | `nomad job run nomad/hello.nomad` | ⚠️ Executed (Host port 8080 occupied by Jenkins service; Nomad Windows Docker driver requires Windows Container mode or Linux agent context) |
| Loki readiness & log push | `python monitoring/send_logs.py` | ✅ Passed (HTTP 204 received) |
| Loki query verification | `/loki/api/v1/query_range` | ✅ Passed (Log line retrieved & verified) |
| Linux script execution | `wsl bash scripts/sysinfo.sh` | ✅ Passed |
| Line endings & secrets scan | `git diff --check`, `git grep` | ✅ Passed (LF line endings, 0 secrets) |

---

## 13. Limitations & Environmental Notes

1. **Host Port 8080 Occupancy:** Host port 8080 on the Windows environment is bound by an existing system service (`Jenkins`, PID 7336). Local standalone testing used host port `8081` (`PORT=8081 python hello.py`) and container port mapping `18080:8080`, preserving internal container port `8080` and application configuration.
2. **Nomad Windows Docker Driver:** The Nomad job specification was validated successfully using `nomad job validate nomad/hello.nomad`. The job uses a Linux Docker image hosted on GHCR (`ghcr.io/mukkarasaikrishnareddy/devops-hello:latest`). On the native Windows Nomad agent, the Docker driver reported that Docker was configured for Linux containers and requested Windows containers (`Docker is configured with Linux containers; switch to Windows Containers`). Therefore, the job was not claimed as successfully deployed on the native Windows agent. The job specification is syntactically valid HCL and is intended to run in a Linux or WSL2-based Nomad environment.

---

## 14. Evidence Screenshots

![GitHub Actions success](screenshots/github-actions-success.png)

![Docker build and application test](screenshots/docker-build-run.png)

![Linux system information](screenshots/linux-sysinfo.png)

---

## 15. Repository Link

[https://github.com/mukkarasaikrishnareddy/devops-intern-final](https://github.com/mukkarasaikrishnareddy/devops-intern-final)
