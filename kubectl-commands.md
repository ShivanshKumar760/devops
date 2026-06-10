---

# Official Documentation

* https://kubernetes.io/docs/home/
* https://kubernetes.io/docs/reference/kubectl/quick-reference/

---

# Kubectl Commands

# Pod Creation

- `kubectl run nginx --image=nginx` # Create a pod named nginx with the nginx image.

# Deployment and Service Creation

- `kubectl create deploy nginx-deploy --image=nginx` # Create a deployment named nginx-deploy with the nginx image.
- `kubectl expose deploy nginx-deploy --port=80` # Expose the nginx-deploy deployment on port 80.

# Describing Resources

- `kubectl describe resourcetype resource name` # General command to describe a resource.
- `kubectl describe pod nginx` # Describe the pod named nginx.

# Viewing Logs

- `kubectl logs nginx` # View logs for the pod named nginx.
- `kubectl logs -f resourcetype/name` #View logs in watch mode

# Execute the bash of a Pod

- `kubectl exec -it pod_name sh ` # To get direct access into the pod shell
- `kubectl exec -it pod_name bash_command ` # To execute a single command directly

# Getting Resources

- `kubectl get pods` # List all pods.
- `kubectl get deploy` # List all deployments.
- `kubectl get svc` # List all services.
- `kubectl get ep` # List all endpoints.

# Editing Resources

- `kubectl edit deploy deployname` # Edit a deployment by name.

# Rollout Management

- `kubectl rollout status` # Check the status of a rollout.
- `kubectl rollout restart deployname` # Restart a deployment.
- `kubectl rollout undo deployname` # Undo the last rollout of a deployment.

# Applying / Deleting Configuration Files

- `kubectl create -f filename` # Create resources from a file.
- `kubectl apply -f filename` # Apply changes to resources from a file.

- `kubectl delete -f filename` # delete changes to resources from a file.

- `kubectl apply -f .` # Apply changes to resources from a current directory containing more than one manifest file

- `kubectl delete -f .` # delete changes to resources from a current directory containing more than one manifest file
