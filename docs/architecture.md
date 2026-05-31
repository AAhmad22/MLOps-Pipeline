# Architecture

## Pipeline overview

```mermaid
flowchart LR
    A[git push to main] --> B[GitHub Actions]
    B --> C{Lint + Tests}
    C -- fail --> X[Pipeline stops]
    C -- pass --> D[Build Docker image]
    D --> E[Push to GHCR registry]
    E --> F[Deploy to EKS]
    F --> G[Pods behind LoadBalancer]
    G --> H[Prometheus scrapes /metrics]
    H --> I[Grafana / CloudWatch dashboards]
```

## Request flow at inference time

```mermaid
sequenceDiagram
    participant U as Client
    participant LB as LoadBalancer
    participant P as API Pod (FastAPI)
    participant M as ResNet model
    U->>LB: POST /predict (image)
    LB->>P: route to a healthy pod
    P->>P: validate type + size
    P->>M: preprocess + forward pass
    M-->>P: class probabilities
    P-->>U: {label, confidence, probabilities}
    P->>P: increment Prometheus counters
```

## Design decisions

- **Transfer learning (frozen ResNet-18 backbone).** Fast to train, small
  artifact, good accuracy on small datasets.
- **Config from environment variables.** One image, many environments. Class
  names, model path and device are all injectable.
- **Multi-stage Docker build + non-root user.** Smaller, more secure images.
- **Health and metrics endpoints.** `/health` drives Kubernetes probes;
  `/metrics` exposes request counts and latency to Prometheus.
- **Quality gate before build.** The image is only built if lint and tests
  pass, so broken code never reaches the registry.
- **OIDC for AWS auth in CI.** The deploy job assumes an IAM role via OIDC
  rather than storing long-lived access keys as secrets.
