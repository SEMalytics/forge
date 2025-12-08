# Multi-Platform Deployment Pattern

**Category**: Deployment
**Difficulty**: Intermediate
**Tags**: deployment, multi-platform, devops, automation, configuration

## Context

When deploying applications, different platforms (Fly.io, Vercel, AWS, Kubernetes) require different configuration files and deployment strategies.

## Problem

Manually creating platform-specific configuration files is:
- Time-consuming and error-prone
- Requires deep knowledge of each platform
- Hard to maintain consistency across platforms
- Difficult to switch platforms later

## Solution

Use Forge's deployment layer to automatically generate platform-specific configurations from a common project description.

## Supported Platforms

| Platform | Best For | Runtime Support | Config Files |
|----------|----------|-----------------|--------------|
| **Fly.io** | Full-stack apps, APIs | Python, Node, Go | fly.toml, Dockerfile |
| **Vercel** | Frontend, serverless | Node, Next.js | vercel.json |
| **AWS Lambda** | Serverless functions | Python, Node, Go | template.yaml (SAM) |
| **Docker** | Any environment | All | Dockerfile, docker-compose.yml |
| **Kubernetes** | Large-scale apps | All | deployment.yaml, service.yaml |

## Usage

### CLI

```bash
# Generate Fly.io configuration
forge deploy --project my-api --platform flyio

# Generate Kubernetes manifests
forge deploy --project my-service --platform k8s --region us-west-2

# Generate and create PR
forge deploy --project my-api --platform flyio --create-pr
```

### Python API

```python
from forge.layers.deployment import (
    DeploymentGenerator,
    DeploymentConfig,
    Platform
)
from pathlib import Path

# Initialize generator
generator = DeploymentGenerator(Path("./my-project"))

# Create configuration
config = DeploymentConfig(
    platform=Platform.FLYIO,
    project_name="my-api",
    runtime="python",
    entry_point="app.py",
    port=8080,
    environment_vars={"DATABASE_URL": "postgres://..."}
)

# Generate configs
files = generator.generate_configs(config)
print(f"Generated: {files}")
```

## Platform Details

### Fly.io

**Best for:** Full-stack applications, APIs, long-running processes

**Generated files:**
- `fly.toml` - Fly configuration
- `Dockerfile` - Container definition

**Features:**
- Multiple regions
- Automatic HTTPS
- Built-in load balancing
- PostgreSQL integration

**Deploy:**
```bash
forge deploy --project my-api --platform flyio
cd .forge/output/my-api
fly deploy
```

### Vercel

**Best for:** Frontend applications, Next.js, serverless functions

**Generated files:**
- `vercel.json` - Vercel configuration

**Features:**
- Edge network
- Automatic previews
- Serverless functions
- Environment variables

**Deploy:**
```bash
forge deploy --project my-app --platform vercel
cd .forge/output/my-app
vercel deploy
```

### AWS Lambda

**Best for:** Event-driven functions, microservices

**Generated files:**
- `template.yaml` - AWS SAM template

**Features:**
- Pay-per-execution
- Auto-scaling
- AWS service integration
- API Gateway integration

**Deploy:**
```bash
forge deploy --project my-function --platform aws
cd .forge/output/my-function
sam build && sam deploy --guided
```

### Docker

**Best for:** Local development, self-hosting, any environment

**Generated files:**
- `Dockerfile` - Container image
- `docker-compose.yml` - Multi-service orchestration
- `.dockerignore` - Build exclusions

**Features:**
- Environment parity
- Easy local testing
- Portable containers
- Multi-service support

**Deploy:**
```bash
forge deploy --project my-app --platform docker
cd .forge/output/my-app
docker-compose up -d
```

### Kubernetes

**Best for:** Large-scale applications, microservices, enterprise

**Generated files:**
- `k8s/deployment.yaml` - Application deployment
- `k8s/service.yaml` - Service configuration

**Features:**
- Auto-scaling
- Self-healing
- Rolling updates
- Resource management

**Deploy:**
```bash
forge deploy --project my-service --platform k8s
cd .forge/output/my-service
kubectl apply -f k8s/
```

## Configuration Examples

### Python API on Fly.io

```python
config = DeploymentConfig(
    platform=Platform.FLYIO,
    project_name="task-api",
    runtime="python",
    entry_point="app.py",
    port=8080,
    region="lax",  # Los Angeles
    environment_vars={
        "DATABASE_URL": "${DATABASE_URL}",
        "SECRET_KEY": "${SECRET_KEY}"
    }
)
```

**Generates fly.toml:**
```toml
app = "task-api"
primary_region = "lax"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true

[env]
  DATABASE_URL = "${DATABASE_URL}"
  SECRET_KEY = "${SECRET_KEY}"
```

### Next.js on Vercel

```python
config = DeploymentConfig(
    platform=Platform.VERCEL,
    project_name="my-frontend",
    runtime="node",
    entry_point="npm start",
    environment_vars={
        "NEXT_PUBLIC_API_URL": "https://api.example.com"
    }
)
```

**Generates vercel.json:**
```json
{
  "name": "my-frontend",
  "version": 2,
  "builds": [{"src": "package.json", "use": "@vercel/node"}],
  "env": {
    "NEXT_PUBLIC_API_URL": "https://api.example.com"
  }
}
```

### Microservice on Kubernetes

```python
config = DeploymentConfig(
    platform=Platform.KUBERNETES,
    project_name="user-service",
    runtime="python",
    entry_point="app.py",
    port=8080,
    environment_vars={
        "DATABASE_URL": "postgres://postgres/users",
        "REDIS_URL": "redis://redis:6379"
    }
)
```

**Generates k8s/deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: user-service
        image: user-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          value: "postgres://postgres/users"
```

## Best Practices

### 1. Use Environment Variables

```python
# Good: Externalize secrets
environment_vars={
    "API_KEY": "${API_KEY}",
    "DATABASE_URL": "${DATABASE_URL}"
}

# Bad: Hardcode secrets
environment_vars={
    "API_KEY": "sk-1234567890"  # Never do this!
}
```

### 2. Match Platform to Use Case

```python
# Static site / Frontend
platform=Platform.VERCEL

# API / Backend
platform=Platform.FLYIO

# Serverless function
platform=Platform.AWS_LAMBDA

# Enterprise scale
platform=Platform.KUBERNETES
```

### 3. Test Locally First

```bash
# Always test with Docker first
forge deploy --project my-api --platform docker
cd .forge/output/my-api
docker-compose up

# Then deploy to cloud
forge deploy --project my-api --platform flyio
```

### 4. Auto-detect Entry Points

Forge automatically detects:
- Python: `app.py`, `main.py`, `wsgi.py`
- Node: `index.js`, `server.js`, `app.js`
- Go: `main.go`

### 5. Create PRs for Deployment Configs

```bash
# Generate configs and create PR
forge deploy --project my-api --platform flyio --create-pr

# Reviewers can see configs before deployment
```

## Related Patterns

- **docker.md** - Docker-specific patterns
- **kubernetes.md** - K8s best practices
- **pr-workflows.md** - Deployment PR automation
- **environment-management.md** - Managing secrets

## References

- [Deployment Documentation](../../docs/GIT_WORKFLOWS.md#deployment)
- [Deployment Layer](../../src/forge/layers/deployment.py)
- [Fly.io Documentation](https://fly.io/docs/)
- [Vercel Documentation](https://vercel.com/docs)
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
