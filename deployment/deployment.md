## Minikube:

- Start by installing Minikube by following the instructions provided in the official Minikube documentation
- Build the Docker images for the server and client containers using the respective Dockerfiles.
-  Start the Minikube cluster by running the following command:

```bash
minikube start
```
Apply the Kubernetes Deployment YAML files for the server and client containers:

```bash
kubectl apply -f server-deployment.yaml
kubectl apply -f client-deployment.yaml
```

Verify that the server and client containers are running:

```bash
kubectl get pods
```

Access the server container:

```bash
kubectl exec -it <server-pod-name> -- /bin/bash
```
## k3s:

- Install k3s by following the instructions provided in the official k3s documentation
- Build the Docker images for the server and client containers using the respective Dockerfiles.
- Start the k3s cluster.
- Apply the Kubernetes Deployment YAML files for the server and client containers:

```bash
kubectl apply -f server-deployment.yaml
kubectl apply -f client-deployment.yaml
```
Verify that the server and client containers are running:

```bash
kubectl get pods
```
Access the server container:

```bash
kubectl exec -it <server-pod-name> -- /bin/bash
```
## MicroK8s:

- Install MicroK8s by following the instructions provided in the official MicroK8s documentation
   
- Build the Docker images for the server and client containers using the respective Dockerfiles. 
- Start the MicroK8s cluster. 
- Apply the Kubernetes Deployment YAML files for the server and client containers:

```bash
kubectl apply -f server-deployment.yaml
kubectl apply -f client-deployment.yaml
```
Verify that the server and client containers are running:

```bash
kubectl get pods
```
Access the server container:

```bash
kubectl exec -it <server-pod-name> -- /bin/bash
```
