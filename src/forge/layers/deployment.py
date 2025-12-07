"""
Multi-platform deployment orchestration

Supports:
- fly.io
- Vercel
- AWS Lambda
- Docker Compose
- Kubernetes

Generates deployment configurations and handles deployment process.
"""

import os
import json
import yaml
from typing import List, Optional, Dict
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class DeploymentError(ForgeError):
    """Deployment errors"""
    pass


class Platform(Enum):
    """Supported deployment platforms"""
    FLYIO = "flyio"
    VERCEL = "vercel"
    AWS_LAMBDA = "aws"
    DOCKER = "docker"
    KUBERNETES = "k8s"


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    platform: Platform
    project_name: str
    runtime: str  # python, node, go, etc.
    entry_point: str
    environment_vars: Dict[str, str]
    build_command: Optional[str] = None
    start_command: Optional[str] = None
    port: int = 8080
    region: Optional[str] = None


class DeploymentGenerator:
    """
    Generate deployment configurations for various platforms.

    Features:
    - Platform-specific config generation
    - Dockerfile generation
    - Docker Compose setup
    - Kubernetes manifests
    - Environment variable management
    """

    def __init__(self, project_path: Path):
        """
        Initialize deployment generator.

        Args:
            project_path: Path to project directory
        """
        self.project_path = Path(project_path)

        if not self.project_path.exists():
            raise DeploymentError(f"Project path does not exist: {project_path}")

        logger.info(f"Initialized DeploymentGenerator for {project_path}")

    def generate_configs(
        self,
        config: DeploymentConfig,
        output_dir: Optional[Path] = None
    ) -> List[Path]:
        """
        Generate deployment configurations.

        Args:
            config: Deployment configuration
            output_dir: Output directory (defaults to project_path)

        Returns:
            List of generated file paths
        """
        if output_dir is None:
            output_dir = self.project_path

        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Generate platform-specific configs
        if config.platform == Platform.FLYIO:
            files = self._generate_flyio(config, output_dir)
            generated_files.extend(files)

        elif config.platform == Platform.VERCEL:
            files = self._generate_vercel(config, output_dir)
            generated_files.extend(files)

        elif config.platform == Platform.AWS_LAMBDA:
            files = self._generate_aws_lambda(config, output_dir)
            generated_files.extend(files)

        elif config.platform == Platform.DOCKER:
            files = self._generate_docker(config, output_dir)
            generated_files.extend(files)

        elif config.platform == Platform.KUBERNETES:
            files = self._generate_kubernetes(config, output_dir)
            generated_files.extend(files)

        logger.info(f"Generated {len(generated_files)} deployment files")
        return generated_files

    def _generate_flyio(
        self,
        config: DeploymentConfig,
        output_dir: Path
    ) -> List[Path]:
        """Generate fly.io configuration"""
        fly_config = {
            "app": config.project_name,
            "primary_region": config.region or "lax",
            "build": {
                "dockerfile": "Dockerfile"
            },
            "env": config.environment_vars,
            "http_service": {
                "internal_port": config.port,
                "force_https": True,
                "auto_stop_machines": True,
                "auto_start_machines": True,
                "min_machines_running": 0
            },
            "vm": {
                "cpu_kind": "shared",
                "cpus": 1,
                "memory_mb": 256
            }
        }

        fly_path = output_dir / "fly.toml"
        with open(fly_path, "w") as f:
            # Convert to TOML format
            toml_content = self._dict_to_toml(fly_config)
            f.write(toml_content)

        logger.info(f"Generated fly.toml at {fly_path}")

        # Also generate Dockerfile
        dockerfile_path = self._generate_dockerfile(config, output_dir)

        return [fly_path, dockerfile_path]

    def _generate_vercel(
        self,
        config: DeploymentConfig,
        output_dir: Path
    ) -> List[Path]:
        """Generate Vercel configuration"""
        vercel_config = {
            "version": 2,
            "name": config.project_name,
            "builds": [
                {
                    "src": config.entry_point,
                    "use": self._get_vercel_builder(config.runtime)
                }
            ],
            "routes": [
                {
                    "src": "/(.*)",
                    "dest": config.entry_point
                }
            ],
            "env": config.environment_vars
        }

        vercel_path = output_dir / "vercel.json"
        with open(vercel_path, "w") as f:
            json.dump(vercel_config, f, indent=2)

        logger.info(f"Generated vercel.json at {vercel_path}")
        return [vercel_path]

    def _generate_aws_lambda(
        self,
        config: DeploymentConfig,
        output_dir: Path
    ) -> List[Path]:
        """Generate AWS Lambda configuration"""
        # SAM template
        sam_template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Transform": "AWS::Serverless-2016-10-31",
            "Description": f"SAM template for {config.project_name}",
            "Resources": {
                f"{config.project_name}Function": {
                    "Type": "AWS::Serverless::Function",
                    "Properties": {
                        "CodeUri": ".",
                        "Handler": config.entry_point,
                        "Runtime": self._get_aws_runtime(config.runtime),
                        "MemorySize": 256,
                        "Timeout": 30,
                        "Environment": {
                            "Variables": config.environment_vars
                        },
                        "Events": {
                            "Api": {
                                "Type": "Api",
                                "Properties": {
                                    "Path": "/{proxy+}",
                                    "Method": "ANY"
                                }
                            }
                        }
                    }
                }
            }
        }

        template_path = output_dir / "template.yaml"
        with open(template_path, "w") as f:
            yaml.dump(sam_template, f, default_flow_style=False)

        logger.info(f"Generated template.yaml at {template_path}")
        return [template_path]

    def _generate_docker(
        self,
        config: DeploymentConfig,
        output_dir: Path
    ) -> List[Path]:
        """Generate Docker configuration"""
        # Generate Dockerfile
        dockerfile_path = self._generate_dockerfile(config, output_dir)

        # Generate docker-compose.yml
        compose_config = {
            "version": "3.8",
            "services": {
                config.project_name: {
                    "build": ".",
                    "ports": [f"{config.port}:{config.port}"],
                    "environment": config.environment_vars,
                    "restart": "unless-stopped"
                }
            }
        }

        compose_path = output_dir / "docker-compose.yml"
        with open(compose_path, "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False)

        logger.info(f"Generated docker-compose.yml at {compose_path}")

        # Generate .dockerignore
        dockerignore_path = output_dir / ".dockerignore"
        dockerignore_content = """
node_modules
*.pyc
__pycache__
.git
.env
.venv
*.log
.pytest_cache
.coverage
"""
        dockerignore_path.write_text(dockerignore_content.strip())

        return [dockerfile_path, compose_path, dockerignore_path]

    def _generate_kubernetes(
        self,
        config: DeploymentConfig,
        output_dir: Path
    ) -> List[Path]:
        """Generate Kubernetes manifests"""
        k8s_dir = output_dir / "k8s"
        k8s_dir.mkdir(exist_ok=True)

        generated_files = []

        # Deployment manifest
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": config.project_name,
                "labels": {
                    "app": config.project_name
                }
            },
            "spec": {
                "replicas": 2,
                "selector": {
                    "matchLabels": {
                        "app": config.project_name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": config.project_name
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": config.project_name,
                                "image": f"{config.project_name}:latest",
                                "ports": [
                                    {
                                        "containerPort": config.port
                                    }
                                ],
                                "env": [
                                    {"name": k, "value": v}
                                    for k, v in config.environment_vars.items()
                                ],
                                "resources": {
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": "128Mi"
                                    },
                                    "limits": {
                                        "cpu": "500m",
                                        "memory": "512Mi"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }

        deployment_path = k8s_dir / "deployment.yaml"
        with open(deployment_path, "w") as f:
            yaml.dump(deployment, f, default_flow_style=False)

        generated_files.append(deployment_path)

        # Service manifest
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": config.project_name
            },
            "spec": {
                "selector": {
                    "app": config.project_name
                },
                "ports": [
                    {
                        "protocol": "TCP",
                        "port": 80,
                        "targetPort": config.port
                    }
                ],
                "type": "LoadBalancer"
            }
        }

        service_path = k8s_dir / "service.yaml"
        with open(service_path, "w") as f:
            yaml.dump(service, f, default_flow_style=False)

        generated_files.append(service_path)

        logger.info(f"Generated Kubernetes manifests in {k8s_dir}")
        return generated_files

    def _generate_dockerfile(
        self,
        config: DeploymentConfig,
        output_dir: Path
    ) -> Path:
        """Generate Dockerfile based on runtime"""
        if config.runtime == "python":
            dockerfile_content = f"""
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE {config.port}

# Run application
CMD {config.start_command or 'python app.py'}
""".strip()

        elif config.runtime == "node":
            dockerfile_content = f"""
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy application
COPY . .

# Build if needed
{f'RUN {config.build_command}' if config.build_command else ''}

# Expose port
EXPOSE {config.port}

# Run application
CMD {config.start_command or '["node", "index.js"]'}
""".strip()

        elif config.runtime == "go":
            dockerfile_content = f"""
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source
COPY . .

# Build
RUN go build -o main {config.entry_point}

# Final stage
FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/main .

EXPOSE {config.port}

CMD ["./main"]
""".strip()

        else:
            # Generic Dockerfile
            dockerfile_content = f"""
FROM ubuntu:latest

WORKDIR /app

COPY . .

EXPOSE {config.port}

CMD {config.start_command or 'echo "Configure start command"'}
""".strip()

        dockerfile_path = output_dir / "Dockerfile"
        dockerfile_path.write_text(dockerfile_content)

        logger.info(f"Generated Dockerfile at {dockerfile_path}")
        return dockerfile_path

    def _dict_to_toml(self, data: Dict, indent: int = 0) -> str:
        """Convert dict to TOML format"""
        lines = []
        indent_str = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                # Section header
                lines.append(f"\n[{key}]")
                # Recursively convert nested dict
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, dict):
                        lines.append(f"\n[{key}.{nested_key}]")
                        lines.append(self._dict_to_toml(nested_value, indent + 1))
                    else:
                        lines.append(f"{indent_str}{nested_key} = {self._toml_value(nested_value)}")
            else:
                lines.append(f"{indent_str}{key} = {self._toml_value(value)}")

        return "\n".join(lines)

    def _toml_value(self, value) -> str:
        """Format value for TOML"""
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            return "[" + ", ".join(self._toml_value(v) for v in value) + "]"
        else:
            return str(value)

    def _get_vercel_builder(self, runtime: str) -> str:
        """Get Vercel builder for runtime"""
        builders = {
            "node": "@vercel/node",
            "python": "@vercel/python",
            "go": "@vercel/go",
            "ruby": "@vercel/ruby"
        }
        return builders.get(runtime, "@vercel/node")

    def _get_aws_runtime(self, runtime: str) -> str:
        """Get AWS Lambda runtime identifier"""
        runtimes = {
            "python": "python3.11",
            "node": "nodejs18.x",
            "go": "go1.x",
            "ruby": "ruby3.2"
        }
        return runtimes.get(runtime, "python3.11")
