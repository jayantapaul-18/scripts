#!/bin/bash

# Get all jobs in all namespaces and output in JSON format
kubectl get jobs --all-namespaces -o json | \
jq -r '.items[] | select(.apiVersion != "batch/v1") | "Namespace: \(.metadata.namespace), Job: \(.metadata.name), apiVersion: \(.apiVersion)"'
