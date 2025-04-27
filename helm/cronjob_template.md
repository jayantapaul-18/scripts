Helm template for a Kubernetes `CronJob` resource, making its parameters configurable via a `values.yaml` file.

**1. Directory Structure**

Create a simple Helm chart structure:

```
my-cronjob-chart/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── _helpers.tpl
    └── cronjob.yaml
```

**2. `Chart.yaml`**

This file contains metadata about your chart.

```yaml
# my-cronjob-chart/Chart.yaml
apiVersion: v2
name: my-cronjob
description: A Helm chart for deploying a configurable Kubernetes CronJob
type: application
version: 0.1.0 # Chart version
appVersion: "1.0" # Version of the application being deployed (optional)
```

**3. `values.yaml`**

This file defines the default configuration values. Users will override these when installing the chart.

```yaml
# my-cronjob-chart/values.yaml

# -- CronJob specific settings
nameOverride: "" # Override the name of the cronjob resource
fullnameOverride: "" # Override the full name of the cronjob resource

schedule: "*/5 * * * *" # Cron schedule (e.g., every 5 minutes)
suspend: false # Set to true to disable the cronjob without deleting it
concurrencyPolicy: Allow # Allow, Forbid, Replace
successfulJobsHistoryLimit: 3 # How many successful job completions to keep
failedJobsHistoryLimit: 1 # How many failed job completions to keep
startingDeadlineSeconds: null # Optional deadline in seconds for starting the job if it misses its schedule

# -- Job template specific settings (Pod definition)
restartPolicy: OnFailure # Never or OnFailure

# -- Service Account for the Job's Pods
serviceAccount:
  # Specifies whether a service account should be created
  create: true
  # The name of the service account to use.
  # If not set and create is true, a name is generated using the fullname template
  name: ""
  # Annotations to add to the service account
  annotations: {}

# -- Container specific settings
image:
  repository: busybox # Container image repository
  pullPolicy: IfNotPresent # Image pull policy (Always, Never, IfNotPresent)
  tag: "latest" # Image tag

# -- Secrets for pulling images from private registries
imagePullSecrets: []
# - name: my-registry-secret

# -- Command and arguments to run in the container
command: []
# - /bin/sh
# - -c
args: []
# - date; echo "Hello from Kubernetes cluster"

# -- Environment variables for the container
env: []
# - name: MY_VARIABLE
#   value: "my_value"
# - name: MY_SECRET_VAR
#   valueFrom:
#     secretKeyRef:
#       name: my-secret
#       key: secret-key

# -- Environment variables from ConfigMaps or Secrets
envFrom: []
# - configMapRef:
#     name: my-configmap
# - secretRef:
#     name: my-secret

# -- Resource requests and limits for the container
resources: {}
  # We usually recommend not to specify default resources and to leave this as a conscious
  # choice for the user. This also increases chances charts run on environments with little
  # resources, such as Minikube. If you do want to specify resources, uncomment the following
  # lines, adjust them as necessary, and remove the curly braces after 'resources:'.
  # limits:
  #   cpu: 100m
  #   memory: 128Mi
  # requests:
  #   cpu: 100m
  #   memory: 128Mi

# -- Volume mounts for the container
volumeMounts: []
# - name: config-volume
#   mountPath: /etc/config

# -- Volumes definition for the Pod
volumes: []
# - name: config-volume
#   configMap:
#     name: my-special-config

# -- Pod security context
podSecurityContext: {}
  # fsGroup: 2000

# -- Container security context
securityContext: {}
  # capabilities:
  #   drop:
  #   - ALL
  # readOnlyRootFilesystem: true
  # runAsNonRoot: true
  # runAsUser: 1000

# -- Node selection constraints
nodeSelector: {}

# -- Tolerations for scheduling
tolerations: []

# -- Affinity rules for scheduling
affinity: {}

# -- Additional labels for the CronJob resource
labels: {}

# -- Additional annotations for the CronJob resource
annotations: {}

# -- Additional labels for the Pods created by the CronJob
podLabels: {}

# -- Additional annotations for the Pods created by the CronJob
podAnnotations: {}
```

**4. `templates/_helpers.tpl`**

This file contains template helpers, often used for generating names and labels consistently.

```gotemplate
{{/* my-cronjob-chart/templates/_helpers.tpl */}}

{{/* vim: set filetype=gotpl: */}}
{{- /*
Expand the name of the chart.
*/}}
{{- define "my-cronjob.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- /*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "my-cronjob.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- /*
Create chart name and version as used by the chart label.
*/}}
{{- define "my-cronjob.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- /*
Common labels
*/}}
{{- define "my-cronjob.labels" -}}
helm.sh/chart: {{ include "my-cronjob.chart" . }}
{{ include "my-cronjob.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.labels }}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{- /*
Selector labels
*/}}
{{- define "my-cronjob.selectorLabels" -}}
app.kubernetes.io/name: {{ include "my-cronjob.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- /*
Create the name of the service account to use
*/}}
{{- define "my-cronjob.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "my-cronjob.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
```

**5. `templates/cronjob.yaml`**

This is the main template file that generates the Kubernetes `CronJob` manifest.

```gotemplate
{{/* my-cronjob-chart/templates/cronjob.yaml */}}
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {{ include "my-cronjob.fullname" . }}
  labels:
    {{- include "my-cronjob.labels" . | nindent 4 }}
  {{- with .Values.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  schedule: {{ .Values.schedule | quote }}
  {{- if .Values.startingDeadlineSeconds }}
  startingDeadlineSeconds: {{ .Values.startingDeadlineSeconds }}
  {{- end }}
  concurrencyPolicy: {{ .Values.concurrencyPolicy }}
  suspend: {{ .Values.suspend }}
  successfulJobsHistoryLimit: {{ .Values.successfulJobsHistoryLimit }}
  failedJobsHistoryLimit: {{ .Values.failedJobsHistoryLimit }}
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            {{- include "my-cronjob.selectorLabels" . | nindent 12 }}
            {{- with .Values.podLabels }}
            {{- toYaml . | nindent 12 }}
            {{- end }}
          {{- with .Values.podAnnotations }}
          annotations:
            {{- toYaml . | nindent 12 }}
          {{- end }}
        spec:
          {{- with .Values.imagePullSecrets }}
          imagePullSecrets:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          serviceAccountName: {{ include "my-cronjob.serviceAccountName" . }}
          {{- with .Values.podSecurityContext }}
          securityContext:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          restartPolicy: {{ .Values.restartPolicy }}
          containers:
            - name: {{ .Chart.Name }}
              {{- with .Values.securityContext }}
              securityContext:
                {{- toYaml . | nindent 16 }}
              {{- end }}
              image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
              imagePullPolicy: {{ .Values.image.pullPolicy }}
              {{- if .Values.command }}
              command:
                {{- toYaml .Values.command | nindent 16 }}
              {{- end }}
              {{- if .Values.args }}
              args:
                {{- toYaml .Values.args | nindent 16 }}
              {{- end }}
              {{- with .Values.env }}
              env:
                {{- toYaml . | nindent 16 }}
              {{- end }}
              {{- with .Values.envFrom }}
              envFrom:
                {{- toYaml . | nindent 16 }}
              {{- end }}
              {{- with .Values.resources }}
              resources:
                {{- toYaml . | nindent 16 }}
              {{- end }}
              {{- with .Values.volumeMounts }}
              volumeMounts:
                {{- toYaml . | nindent 16 }}
              {{- end }}
          {{- with .Values.volumes }}
          volumes:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.nodeSelector }}
          nodeSelector:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.affinity }}
          affinity:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.tolerations }}
          tolerations:
            {{- toYaml . | nindent 12 }}
          {{- end }}

{{- /* Optionally include ServiceAccount definition if create is true */}}
{{- if .Values.serviceAccount.create }}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "my-cronjob.serviceAccountName" . }}
  labels:
    {{- include "my-cronjob.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}

```

**Explanation:**

1.  **`values.yaml`**: This file holds all the user-configurable parameters with sensible defaults. Users can create their own `my-values.yaml` file and use `helm install my-release ./my-cronjob-chart -f my-values.yaml` to override these defaults.
2.  **`_helpers.tpl`**: Defines reusable template snippets.
    * `my-cronjob.name`: Generates the base name for resources.
    * `my-cronjob.fullname`: Generates the full name, typically including the Helm release name.
    * `my-cronjob.chart`: Generates the chart name and version label.
    * `my-cronjob.labels`: Generates a standard set of labels, including custom ones from `values.yaml`.
    * `my-cronjob.selectorLabels`: Generates labels used for selecting resources belonging to this chart instance.
    * `my-cronjob.serviceAccountName`: Determines the name of the ServiceAccount to use or create.
3.  **`templates/cronjob.yaml`**:
    * Uses `{{ include "..." . }}` to call helper templates for names and labels.
    * Accesses values from `values.yaml` using the `.` context (e.g., `.Values.schedule`, `.Values.image.repository`).
    * Uses `{{ | quote }}` for string values like the schedule to ensure they are correctly formatted in YAML.
    * Uses `{{- with .Values... }}` or `{{- if .Values... }}` blocks to conditionally include sections only if the corresponding value is set in `values.yaml`. This prevents empty sections in the generated YAML.
    * Uses `{{ toYaml . | nindent N }}` to correctly format and indent complex structures like `resources`, `env`, `volumeMounts`, `volumes`, `nodeSelector`, `tolerations`, `affinity`, `annotations`, etc. `nindent N` ensures the generated YAML has the correct indentation level.
    * Includes an optional `ServiceAccount` definition controlled by `Values.serviceAccount.create`.

**How to Use:**

1.  Save these files in the directory structure shown above.
2.  Customize the `values.yaml` file with your desired defaults.
3.  Install the chart using Helm:
    * `helm install my-cronjob-release ./my-cronjob-chart` (using defaults)
    * `helm install my-cronjob-release ./my-cronjob-chart --set schedule="0 0 * * *"` (override a single value)
    * Create a `custom-values.yaml` file and run `helm install my-cronjob-release ./my-cronjob-chart -f custom-values.yaml` (override multiple values).
4.  Check the status: `kubectl get cronjobs`
