To create a Streamlit app that displays all the Kubernetes pods' details using the Kubernetes API library (`kubernetes` Python client), you'll need to set up the environment and write a Python script to interact with the Kubernetes API. 

First, ensure you have the required libraries installed:
```bash
pip install streamlit kubernetes
```

Here's a basic Streamlit app script:

```python
import streamlit as st
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def get_kubernetes_pods():
    """Fetches all pods in the Kubernetes cluster."""
    try:
        # Load the in-cluster config or from the kubeconfig file
        config.load_kube_config()
        # Alternatively, for in-cluster:
        # config.load_incluster_config()

        v1 = client.CoreV1Api()
        pods = v1.list_pod_for_all_namespaces(watch=False)
        return pods.items
    except ApiException as e:
        st.error(f"Exception when calling CoreV1Api->list_pod_for_all_namespaces: {e}")
        return []

def display_pod_details(pods):
    """Displays the details of the pods in a table format."""
    if not pods:
        st.write("No pods found.")
        return

    pod_data = []
    for pod in pods:
        pod_info = {
            "Namespace": pod.metadata.namespace,
            "Name": pod.metadata.name,
            "Node": pod.spec.node_name,
            "Status": pod.status.phase,
            "IP": pod.status.pod_ip,
            "Start Time": pod.status.start_time,
        }
        pod_data.append(pod_info)

    # Display in Streamlit
    st.write("## Kubernetes Pods Details")
    st.dataframe(pod_data)

def main():
    st.title("Kubernetes Pods Viewer")
    st.write("This app displays all the Kubernetes pods' details using the Kubernetes API.")

    pods = get_kubernetes_pods()
    display_pod_details(pods)

if __name__ == "__main__":
    main()
```

### Steps to Run the Streamlit App

1. Save the script in a file, e.g., `k8s_pods_viewer.py`.
2. Run the app using Streamlit:
   ```bash
   streamlit run k8s_pods_viewer.py
   ```
3. The app will open in your default web browser and display the details of the Kubernetes pods.

### Additional Notes

- The app assumes that you have access to a Kubernetes cluster and the proper credentials to query the API.
- Ensure your environment has access to the cluster either by being in-cluster (running inside a pod) or by having access to a `kubeconfig` file locally.
- You can expand this app to add filtering, sorting, or more detailed views of each pod.
