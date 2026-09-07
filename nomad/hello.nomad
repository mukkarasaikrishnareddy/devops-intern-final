job "hello" {
  datacenters = ["dc1"]
  type        = "service"

  group "hello" {
    count = 1

    network {
      port "http" {
        static = 8080
      }
    }

    service {
      name = "hello"
      port = "http"

      check {
        type     = "http"
        path     = "/"
        interval = "10s"
        timeout  = "2s"
      }
    }

    task "hello" {
      driver = "docker"

      config {
        # Image published to GitHub Container Registry via the CI/CD pipeline.
        # The image is public; no registry auth is required.
        image = "ghcr.io/mukkarasaikrishnareddy/devops-hello:latest"
        ports = ["http"]

        # Force Nomad to always pull the latest image on each job run.
        force_pull = true
      }

      resources {
        cpu    = 100   # MHz
        memory = 128   # MB
      }
    }
  }
}
