# MLOps Image Classifier
[CI/CD](https://github.com/AAhmad22/MLOps-Pipeline/actions/workflows/ci-cd.yml/badge.svg)An end-to-end machine learning deployment pipeline: a PyTorch image classifier
served as a containerised microservice, continuously tested and built by CI/CD,
deployed to Kubernetes (AWS EKS), and monitored with Prometheus.

This project demonstrates the full lifecycle of getting a model into
production — not just training it, but **shipping, scaling and observing it.**

---

## What this demonstrates

| Area | Shown by |
|------|----------|
| ML / PyTorch | Transfer-learning classifier (`src/model.py`, `src/train.py`) |
| Model serving | FastAPI inference API (`src/app.py`, `src/predict.py`) |
| Containerisation | Multi-stage `Dockerfile`, non-root user, healthcheck |
| CI/CD | GitHub Actions: lint → test → build → push → deploy |
| Kubernetes / EKS | `k8s/` manifests with probes, autoscaling, LoadBalancer |
| Monitoring | Prometheus metrics endpoint + scrape config |
| Cloud (AWS) | GHCR/ECR images, EKS deploy via OIDC |

## Architecture

```
git push ─► GitHub Actions ─► lint + test ─► build image ─► push to registry
                                                                  │
                                                                  ▼
                              Prometheus ◄── EKS pods ◄── deploy (kubectl)
                                                │
                                          LoadBalancer ─► clients
```

See [`docs/architecture.md`](docs/architecture.md) for detailed diagrams.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness/readiness probe |
| GET | `/metrics` | Prometheus metrics |
| POST | `/predict` | Classify an uploaded image |

Example:

```bash
curl -X POST http://localhost:8000/predict \
  -F "file=@cat.jpg"
# {"label":"cat","confidence":0.97,"probabilities":{"cat":0.97,"dog":0.03}}
```

## Quickstart (local)

```bash
# 1. Install dependencies
make install

# 2. Run the tests
make test

# 3. Train a model (expects data/train and data/val ImageFolder layout)
make train

# 4. Serve the API
make serve   # http://localhost:8000/docs
```

Or run the whole stack (API + Prometheus) with Docker:

```bash
make compose-up
# API:        http://localhost:8000/docs
# Prometheus: http://localhost:9090
```

## Training data layout

```
data/
  train/
    cat/   *.jpg
    dog/   *.jpg
  val/
    cat/   *.jpg
    dog/   *.jpg
```

Swap in any classes by setting `CLASS_NAMES` (e.g. `CLASS_NAMES="healthy,defective"`).

## Deploying to EKS

1. Build and push an image (CI does this automatically on `main`).
2. Point the manifest at your image:
   ```bash
   sed -i "s#IMAGE_PLACEHOLDER#ghcr.io/<you>/mlops-image-classifier:latest#" k8s/deployment.yaml
   kubectl apply -f k8s/
   ```
3. Get the external URL:
   ```bash
   kubectl get service image-classifier
   ```

To automate the deploy step, add `AWS_ROLE_ARN`, `AWS_REGION` and `EKS_CLUSTER`
as repository secrets and uncomment the `deploy` job in
`.github/workflows/ci-cd.yml`.

## Tech stack

PyTorch · torchvision · FastAPI · Docker · GitHub Actions · Kubernetes (EKS) ·
Prometheus · Python 3.11

## Roadmap

- [ ] Add Grafana dashboards for the Prometheus metrics
- [ ] Model versioning / experiment tracking (MLflow)
- [ ] Terraform module to provision the EKS cluster
- [ ] Data + model drift detection

## License

MIT
