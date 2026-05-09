# Docker Networking Demo

A hands-on Node.js project to understand how Docker networking works —
how containers talk to each other and how they reach the outside world.

---

## Project Structure

```
docker-networking-demo/
├── api-service/          # Main service (port 3000)
│   ├── index.js
│   ├── package.json
│   └── Dockerfile
├── ping-service/         # Internal-only service (port 4000 - not exposed)
│   ├── index.js
│   ├── package.json
│   └── Dockerfile
├── frontend/
│   └── index.html        # Visual dashboard — open in browser
├── docker-compose.yml
└── README.md
```

---

## How to Run

```bash
# 1. Build and start all containers
docker-compose up --build

# 2. Open the dashboard in your browser
open frontend/index.html

# Or just hit the APIs directly:
curl http://localhost:3000/info
curl http://localhost:3000/talk-to-ping
curl http://localhost:3000/external
curl http://localhost:3000/network
curl http://localhost:5000/info   # isolated-service
```

---

## What This Demonstrates

### 1. Container Identity (/info)

Each container gets:

- A unique hostname (short container ID)
- An internal IP in the Docker bridge network (172.x.x.x)
  This IP is NOT your machine's IP — it's a virtual address inside Docker's network.

### 2. Inter-Container Communication via Internal DNS (/talk-to-ping)

api-service calls:
http://ping-service:4000/pong

No IP address needed. Docker's built-in DNS resolves "ping-service" (the
container name) to its internal IP automatically. This only works because
both containers are on the same network (app-network).

### 3. Reaching the External Internet (/external)

Containers can call external APIs through Docker's NAT.
Outbound traffic exits via the host machine's real IP.
The external server never sees the 172.x.x.x container address.

### 4. Network Interfaces (/network)

Inside a container you'll see:

- eth0: The virtual NIC Docker creates (172.x.x.x)
- lo: Loopback / localhost inside the container

### 5. Network Isolation (isolated-service on port 5000)

isolated-service is on a DIFFERENT Docker network.

- Your browser CAN reach it via port mapping (localhost:5000)
- api-service CANNOT reach it internally (different network = isolated)

---

## Networks Explained

```
app-network (bridge)
├── api-service      ← exposed to host on :3000
└── ping-service     ← internal only, no port mapping

isolated-network (bridge)
└── isolated-service ← exposed to host on :5000, but isolated from app-network
```

---

## Key Concepts

| Concept           | What It Means                                                    |
| ----------------- | ---------------------------------------------------------------- |
| Bridge network    | Virtual switch Docker creates. Containers on it can talk freely. |
| Internal DNS      | Docker resolves container names to IPs automatically.            |
| Port mapping      | host:container — punches hole for external access                |
| NAT               | How containers reach the internet via the host's IP              |
| Network isolation | Different networks = no communication, even on same host         |

---

## Useful Commands

```bash
# See all Docker networks
docker network ls

# Inspect a network (see which containers are on it)
docker network inspect app-network

# See container IPs
docker inspect api-service | grep IPAddress

# Run a shell inside a container
docker exec -it api-service sh

# From inside api-service, ping ping-service by name
docker exec -it api-service ping ping-service

# From inside api-service, try to ping isolated-service (will fail!)
docker exec -it api-service ping isolated-service
```
