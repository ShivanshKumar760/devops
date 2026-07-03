# ---------- Stage 1: deps ----------
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
# Pure JS packages install instantly without native tools
RUN npm ci --omit=dev

# ---------- Stage 2: build ----------
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# ---------- Stage 3: runtime ----------
FROM node:20-alpine AS runtime

ENV NODE_ENV=production
WORKDIR /app

RUN chown -R node:node /app
USER node

# Copy files before node_modules so local files don't overwrite container modules
COPY --chown=node:node . .
COPY --chown=node:node --from=deps /app/node_modules ./node_modules

EXPOSE 5001

# FIXED: Points directly to your new secure /health route
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "fetch('http://localhost:5001/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "index.js"]
