Document: Deploying a Streamlit App with .streamlit Configuration and Kubernetes

1. Introduction

This document provides a step-by-step guide to deploy a Streamlit application using Kubernetes with the .streamlit configuration. The .streamlit folder is used to store configuration files for Streamlit, which control various aspects of the app’s behavior.

We’ll go through the following steps:

	•	Creating a .streamlit configuration file.
	•	Dockerizing the Streamlit application.
	•	Setting up a Kubernetes cluster.
	•	Deploying the Streamlit app to Kubernetes.

2. Prerequisites

	•	A working Streamlit app.
	•	Docker installed on your machine.
	•	Access to a Kubernetes cluster (either locally using Minikube, or a cloud provider like GKE, EKS, or AKS).
	•	Kubectl command-line tool configured to interact with your cluster.
	•	Helm installed (optional, but helpful for managing Kubernetes applications).

3. Step 1: Create .streamlit Configuration File

The .streamlit directory allows customization of your Streamlit app, including setting the server port, enabling CORS, or adjusting other settings.

	1.	Create a folder called .streamlit in the root of your project directory.

mkdir .streamlit


	2.	Inside the .streamlit directory, create a file called config.toml and add the following configurations:

# .streamlit/config.toml
[server]
headless = true
enableCORS = false
port = $PORT

	•	headless: Ensures the app runs in headless mode for deployment.
	•	enableCORS: Set to false to allow access from different domains (you may modify this based on your security needs).
	•	port: Uses the $PORT environment variable, which is needed when deploying on platforms that assign dynamic ports (like Heroku).

4. Step 2: Dockerizing the Streamlit App

Next, create a Docker image of your Streamlit app to deploy it in Kubernetes.

	1.	Create a Dockerfile in the root directory of your Streamlit app:

# Dockerfile
FROM python:3.9-slim

# Install dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app to the Docker image
COPY . /app
WORKDIR /app

# Expose the Streamlit port
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501

# Run the Streamlit app
CMD ["streamlit", "run", "app.py"]


	2.	Build the Docker image:

docker build -t streamlit-app .


	3.	Test the Docker image locally:

docker run -p 8501:8501 streamlit-app

Your Streamlit app should now be accessible on http://localhost:8501.

5. Step 3: Setting Up Kubernetes

You can either use a cloud provider (like Google Kubernetes Engine, Amazon EKS, etc.) or set up Kubernetes locally using Minikube.

	1.	Initialize Minikube (optional) if you’re using it locally:

minikube start


	2.	Configure kubectl to work with your Kubernetes cluster (this is typically done automatically when setting up the cluster).

6. Step 4: Deploying to Kubernetes

Now that your Docker image is ready, we can deploy it to Kubernetes.

6.1. Create Kubernetes Deployment YAML

	1.	Create a Kubernetes deployment configuration in a YAML file (streamlit-deployment.yaml):

apiVersion: apps/v1
kind: Deployment
metadata:
  name: streamlit-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: streamlit
  template:
    metadata:
      labels:
        app: streamlit
    spec:
      containers:
      - name: streamlit
        image: streamlit-app:latest
        ports:
        - containerPort: 8501
        env:
        - name: PORT
          value: "8501"


	2.	Create a Kubernetes Service YAML (streamlit-service.yaml) to expose the application:

apiVersion: v1
kind: Service
metadata:
  name: streamlit-service
spec:
  type: LoadBalancer
  selector:
    app: streamlit
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8501



6.2. Deploy the App to Kubernetes

	1.	Apply the Deployment and Service:

kubectl apply -f streamlit-deployment.yaml
kubectl apply -f streamlit-service.yaml


	2.	Verify the Deployment:
Check the status of the pods and services:

kubectl get pods
kubectl get svc

The service should be accessible at the external IP provided by the kubectl get svc output.

7. Step 5: Scaling and Monitoring the App

You can easily scale the number of replicas for your Streamlit app using:

kubectl scale deployment streamlit-app --replicas=5

To monitor your deployment, you can check the logs of a specific pod:

kubectl logs <pod-name>

8. Conclusion

By following the steps in this document, you’ve successfully:

	•	Created a .streamlit configuration file.
	•	Dockerized your Streamlit app.
	•	Deployed your app to a Kubernetes cluster.

This setup is flexible and scalable, making it suitable for production deployments of your Streamlit applications.