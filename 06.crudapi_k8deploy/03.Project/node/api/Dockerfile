# ---------- Stage 1: deps ----------
# Installs dependencies in isolation so this layer is cached
# and only re-runs when package.json / package-lock.json change.
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# ---------- Stage 2: build ----------
# Kept separate from "deps" so devDependencies (linters, bundlers,
# type-checkers, etc.) can be installed here without bloating the
# final image. Safe to keep even if you don't have a build step today.
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# If you add a build/transpile step later (e.g. tsc, esbuild), run it here:
# RUN npm run build

# ---------- Stage 3: runtime ----------
# Minimal final image: only production node_modules + source files.
# No build tools, no devDependencies, no npm cache left behind.
FROM node:20-alpine AS runtime

ENV NODE_ENV=production
WORKDIR /app

# Run as a non-root user (alpine's built-in "node" user)
RUN chown -R node:node /app
USER node

COPY --chown=node:node --from=deps /app/node_modules ./node_modules
COPY --chown=node:node package.json ./
COPY --chown=node:node . .

EXPOSE 5001

# Basic container-level healthcheck. There's no dedicated /health route
# in this API yet, so this hits /feed as a lightweight liveness signal —
# swap it for a real /health endpoint if you add one.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "fetch('http://localhost:5001/feed').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "index.js"]