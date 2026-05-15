# Docker Complete Notes & Command Reference

# 1. What is Docker?

Docker is a containerization platform that packages an application with all dependencies, libraries, and configuration into a **container**.

## Key Concepts

- **Image** → Blueprint/template for containers
- **Container** → Running instance of an image
- **Dockerfile** → Instructions to build an image
- **Volume** → Persistent storage
- **Network** → Communication layer between containers
- **Registry** → Stores images (Docker Hub)

---

# 2. Docker Architecture

## Components

- Docker Client (`docker` command)
- Docker Daemon (`dockerd`)
- Docker Host
- Docker Registry

## Flow

```txt
Dockerfile → Docker Image → Docker Container
```

---

# 3. Docker Installation Check

```bash
docker --version
docker info
```

---

# 4. Basic Docker Commands Cheat Sheet

## Images

### List images
```bash
docker images
```

### Pull image from Docker Hub
```bash
docker pull nginx
```

### Remove image
```bash
docker rmi nginx
```

### Remove forcefully
```bash
docker rmi -f IMAGE_ID
```

---

## Containers

### Run container
```bash
docker run nginx
```

### Run in detached mode
```bash
docker run -d nginx
```

### Run with port mapping
```bash
docker run -d -p 8080:80 nginx
```

### Run with name
```bash
docker run -d --name mynginx nginx
```

### Interactive shell
```bash
docker run -it ubuntu bash
```

### List running containers
```bash
docker ps
```

### List all containers
```bash
docker ps -a
```

### Stop container
```bash
docker stop CONTAINER_ID
```

### Start container
```bash
docker start CONTAINER_ID
```

### Restart container
```bash
docker restart CONTAINER_ID
```

### Remove container
```bash
docker rm CONTAINER_ID
```

### Force remove running container
```bash
docker rm -f CONTAINER_ID
```

---

# 5. Docker Logs & Debugging

### View logs
```bash
docker logs CONTAINER_ID
```

### Follow logs live
```bash
docker logs -f CONTAINER_ID
```

### Execute inside container
```bash
docker exec -it CONTAINER_ID bash
```

### Inspect container
```bash
docker inspect CONTAINER_ID
```

### Resource usage
```bash
docker stats
```

---

# 6. Dockerfile Complete Guide

## Basic Syntax

```dockerfile
# Base image
FROM node:20-alpine

# Metadata
LABEL maintainer="you@example.com"

# Working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Environment variables
ENV PORT=3000

# Expose port
EXPOSE 3000

# Default command
CMD ["npm", "start"]
```

---

# 7. Dockerfile Instructions Explained

## FROM
Base image
```dockerfile
FROM ubuntu:22.04
```

## WORKDIR
Sets working directory
```dockerfile
WORKDIR /usr/src/app
```

## COPY
Copies local files
```dockerfile
COPY . .
```

## ADD
Like COPY but supports URLs and archives
```dockerfile
ADD app.tar.gz /app
```

## RUN
Executes command during build
```dockerfile
RUN apt-get update && apt-get install -y curl
```

## CMD
Default startup command
```dockerfile
CMD ["node", "server.js"]
```

## ENTRYPOINT
Fixed executable
```dockerfile
ENTRYPOINT ["python"]
```

## ENV
Environment variable
```dockerfile
ENV NODE_ENV=production
```

## ARG
Build-time variable
```dockerfile
ARG VERSION=1.0
```

## USER
Run as non-root
```dockerfile
USER node
```

---

# 8. Docker Layers Explained

Each Dockerfile command creates a layer:

```dockerfile
FROM node:20
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
```

## Layer Order:
1. Base OS layer
2. Working directory layer
3. package.json layer
4. npm install layer
5. source code layer

## Why Layers Matter
- Cached builds
- Faster rebuilds
- Smaller changes

## Optimization Tip
Copy package.json first before source code.

---

# 9. Build Docker Image

## Build syntax
```bash
docker build -t myapp .
```

## Build with version
```bash
docker build -t myapp:v1 .
```

## Build specific Dockerfile
```bash
docker build -f Dockerfile.dev -t myapp-dev .
```

---

# 10. .dockerignore

Exclude files:

```txt
node_modules
.env
.git
Dockerfile
README.md
```

---

# 11. Multi-stage Builds

```dockerfile
FROM node:20 AS builder
WORKDIR /app
COPY . .
RUN npm install && npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

## Benefits
- Smaller final image
- Better security
- Production optimized

---

# 12. Docker Volumes

## What is a Volume?
Persistent storage outside container lifecycle.

## Create volume
```bash
docker volume create myvolume
```

## List volumes
```bash
docker volume ls
```

## Inspect volume
```bash
docker volume inspect myvolume
```

## Remove volume
```bash
docker volume rm myvolume
```

---

## Mount Volume Syntax

```bash
docker run -v myvolume:/app/data nginx
```

## Bind Mount

```bash
docker run -v $(pwd):/app node
```

## Windows Bind Mount
```bash
docker run -v C:/project:/app node
```

---

# 13. Volume Types

## Named Volume
```bash
docker run -v postgres_data:/var/lib/postgresql/data postgres
```

## Anonymous Volume
```bash
docker run -v /app/data nginx
```

## Bind Mount
```bash
docker run -v ./src:/app/src node
```

---

# 14. Docker Networking

## Network Types

### Bridge (default)
```bash
docker network ls
```

### Create custom bridge
```bash
docker network create mynetwork
```

### Run container in network
```bash
docker run -d --network=mynetwork --name app1 nginx
```

### Connect existing container
```bash
docker network connect mynetwork app1
```

### Disconnect
```bash
docker network disconnect mynetwork app1
```

### Inspect network
```bash
docker network inspect mynetwork
```

---

# 15. Port Mapping

```bash
docker run -p HOST_PORT:CONTAINER_PORT nginx
```

Example:
```bash
docker run -p 3000:80 nginx
```

Browser → localhost:3000 → Container:80

---

# 16. Docker Compose

## docker-compose.yml

```yaml
version: "3.9"
services:
  app:
    build: .
    ports:
      - "3000:3000"
    volumes:
      - .:/app
    environment:
      NODE_ENV: development

  db:
    image: postgres
    environment:
      POSTGRES_PASSWORD: password
```

## Commands

### Start
```bash
docker compose up
```

### Detached
```bash
docker compose up -d
```

### Stop
```bash
docker compose down
```

### Rebuild
```bash
docker compose up --build
```

---

# 17. Cleanup Commands

## Remove stopped containers
```bash
docker container prune
```

## Remove unused images
```bash
docker image prune -a
```

## Remove unused volumes
```bash
docker volume prune
```

## Full system cleanup
```bash
docker system prune -a
```

---

# 18. Production Best Practices

## Security
- Use minimal images (`alpine`)
- Avoid root user
- Use `.dockerignore`
- Scan images

## Performance
- Multi-stage builds
- Layer caching
- Reduce dependencies

## Reliability
- Healthchecks
- Restart policies

Example:
```bash
docker run --restart unless-stopped nginx
```

---

# 19. Common Real-World Workflow

## Node App Example

### Step 1: Write Dockerfile
### Step 2: Build image
```bash
docker build -t mynodeapp .
```

### Step 3: Run container
```bash
docker run -d -p 3000:3000 mynodeapp
```

### Step 4: Mount source for dev
```bash
docker run -v $(pwd):/app -p 3000:3000 mynodeapp
```

---

# 20. Interview-Level Docker Concepts

## Difference: CMD vs ENTRYPOINT
- CMD = default command, overridable
- ENTRYPOINT = fixed executable

## Difference: Volume vs Bind Mount
- Volume = Docker managed
- Bind Mount = Host controlled

## Difference: Image vs Container
- Image = Blueprint
- Container = Running process

---

# 21. Useful Advanced Commands

## Save image
```bash
docker save -o myimage.tar myapp
```

## Load image
```bash
docker load -i myimage.tar
```

## Tag image
```bash
docker tag myapp username/myapp:v1
```

## Push to Docker Hub
```bash
docker push username/myapp:v1
```

---

# 22. Docker Troubleshooting

## Container exits immediately
Check:
```bash
docker logs CONTAINER_ID
```

## Port already allocated
```bash
netstat -ano
```

## Permission denied
Use:
```bash
sudo docker
```

---

# 23. Final Learning Path

1. Docker basics
2. Dockerfile
3. Volumes
4. Networking
5. Compose
6. Multi-stage builds
7. Production deployment
8. Kubernetes next

---

# Quick Revision

```txt
docker build → Create image
docker run → Start container
docker ps → List containers
docker exec → Enter container
docker volume → Persistent data
docker network → Container communication
docker compose → Multi-container apps
```

