# ==========================================
# STAGE 1: Build / Dependency Gathering
# ==========================================
FROM node:20-alpine AS build

WORKDIR /app

# Copy lock files together
COPY package*.json ./

# Install only production dependencies cleanly
RUN npm install

# ==========================================
# STAGE 2: Lightweight Production Runtime
# ==========================================
FROM node:20-alpine 

WORKDIR /app

# 1. Bring over ONLY the clean node_modules from Stage 1
COPY --from=build /app/node_modules ./node_modules
COPY package.json ./

# 2. Copy the fresh source code straight from your host machine
COPY src/ ./src/

EXPOSE 3000

# 3. Execute Node directly (allows clean container shutdowns)
CMD [ "node", "src/index.js" ]