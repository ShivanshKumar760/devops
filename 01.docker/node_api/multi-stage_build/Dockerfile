# ----- Stage 1: Build stage -----
FROM node:20-slim AS builder
WORKDIR /app
COPY api/package*.json ./
# Install dependencies
RUN npm install 
COPY api/ ./
# Remove development dependencies to shrink the node_modules size
RUN npm prune --production

# ----- Stage 2: Production stage -----
FROM node:20-slim
WORKDIR /app

# 1. Install MongoDB and immediately clean up caches to keep size small
RUN apt-get update && apt-get install -y \
    gnupg \
    curl \
    && curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
       gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg \
    && echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" \
       | tee /etc/apt/sources.list.d/mongodb-org-7.0.list \
    && apt-get update \
    && apt-get install -y mongodb-org \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy ONLY required application files from builder (Fixes the missing node_modules crash)
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/index.js ./index.js

# 3. Create the MongoDB data directory
RUN mkdir -p /data/db

EXPOSE 3000
EXPOSE 27017

# 4. Start Script: Run MongoDB with optimization flags, then start Node
# --nojournal and --smallfiles (implicit in newer storage engines) prevent huge disk allocation files
# CMD ["sh", "-c", "mongod --bind_ip_all --fork --logpath /var/log/mongodb.log --nojournal && node index.js"]
CMD ["sh", "-c", "mongod --bind_ip_all --fork --logpath /var/log/mongodb.log && node index.js"]