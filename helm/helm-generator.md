Here's a Python script that generates Helm templates based on user input through CLI arguments. This tool will create a basic Helm chart structure with deployment and service templates:

```python
import argparse
import os
import textwrap

def create_helm_chart(args):
    chart_dir = f"./{args.name}/"
    templates_dir = os.path.join(chart_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)

    # Create Chart.yaml
    with open(os.path.join(chart_dir, "Chart.yaml"), "w") as f:
        f.write(f"""apiVersion: v2
name: {args.name}
description: A Helm chart for Kubernetes
type: application
version: {args.version}
appVersion: "{args.app_version}"
""")

    # Create values.yaml
    with open(os.path.join(chart_dir, "values.yaml"), "w") as f:
        f.write(f"""replicaCount: {args.replicas}

image:
  repository: {args.image}
  pullPolicy: IfNotPresent
  tag: "{args.tag}"

service:
  type: {args.service_type}
  port: {args.port}

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 100m
    memory: 128Mi
""")

    # Create deployment template
    deployment_template = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{{{ .Chart.Name }}}}-deployment
  labels:
    app: {{{{ .Chart.Name }}}}
spec:
  replicas: {{{{ .Values.replicaCount }}}}
  selector:
    matchLabels:
      app: {{{{ .Chart.Name }}}}
  template:
    metadata:
      labels:
        app: {{{{ .Chart.Name }}}}
    spec:
      containers:
        - name: {{{{ .Chart.Name }}}}
          image: {{{{ .Values.image.repository }}}}:{{{{ .Values.image.tag }}}}
          imagePullPolicy: {{{{ .Values.image.pullPolicy }}}}
          ports:
            - containerPort: {{{{ .Values.service.port }}}}
          resources:
            {{{{ toYaml .Values.resources | indent 12 }}}}
"""

    # Create service template
    service_template = f"""apiVersion: v1
kind: Service
metadata:
  name: {{{{ .Chart.Name }}}}-service
spec:
  type: {{{{ .Values.service.type }}}}
  ports:
    - port: {{{{ .Values.service.port }}}}
      targetPort: {{{{ .Values.service.port }}}}
  selector:
    app: {{{{ .Chart.Name }}}}
"""

    # Write template files
    with open(os.path.join(templates_dir, "deployment.yaml"), "w") as f:
        f.write(textwrap.dedent(deployment_template))

    with open(os.path.join(templates_dir, "service.yaml"), "w") as f:
        f.write(textwrap.dedent(service_template))

    print(f"Helm chart created successfully in {chart_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Helm chart templates")

    # Required arguments
    parser.add_argument("--name", required=True, help="Name of the application")
    parser.add_argument("--image", required=True, help="Docker image repository")

    # Optional arguments with defaults
    parser.add_argument("--version", default="0.1.0", help="Chart version (default: 0.1.0)")
    parser.add_argument("--app-version", default="1.0.0", help="App version (default: 1.0.0)")
    parser.add_argument("--replicas", type=int, default=1, help="Number of replicas (default: 1)")
    parser.add_argument("--tag", default="latest", help="Docker image tag (default: latest)")
    parser.add_argument("--service-type", default="ClusterIP",
                       choices=["ClusterIP", "NodePort", "LoadBalancer"],
                       help="Kubernetes service type (default: ClusterIP)")
    parser.add_argument("--port", type=int, default=80, help="Service port (default: 80)")

    args = parser.parse_args()
    create_helm_chart(args)
```

To use this tool:

1. Save the script as `helm-generator.py`
2. Run it with required parameters:

```bash
python3 helm-generator.py \
  --name myapp \
  --image myregistry/myapp \
  --version 1.2.3 \
  --app-version 2.0.0 \
  --replicas 3 \
  --tag v1.0 \
  --service-type LoadBalancer \
  --port 8080
```

This will generate a Helm chart with the following structure:

```
./myapp/
├── Chart.yaml
├── templates
│   ├── deployment.yaml
│   └── service.yaml
└── values.yaml
```

Key features:

- Generates basic Kubernetes Deployment and Service templates
- Creates proper Chart.yaml and values.yaml
- Supports common Helm chart structure
- Includes basic configuration options:
  - Replica count
  - Image repository and tag
  - Service type (ClusterIP, NodePort, LoadBalancer)
  - Resource limits/requests
  - Port configuration
  - Version management

We can customize the templates in the script by modifying the template strings (deployment_template and service_template) to match your specific requirements.

To extend this tool, we could add:

1. Ingress template support
2. ConfigMap/Secret generation
3. Horizontal Pod Autoscaler template
4. Custom resource definitions
5. More sophisticated input validation
6. Support for multiple containers in a pod
7. Environment variable configuration
8. Volume mount support
