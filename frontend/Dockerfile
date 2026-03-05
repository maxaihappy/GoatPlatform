# Optional: run Next.js server on Cloud Run (alternative to Firebase Hosting static export)
# Build: docker build -t goat-frontend .
# Run: docker run -p 8080:3000 -e NEXT_PUBLIC_API_URL=https://your-api.run.app goat-frontend
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN mkdir -p /app/public
# Set API URL at build time (Cloud Run backend). Override with: docker build --build-arg NEXT_PUBLIC_API_URL=...
ARG NEXT_PUBLIC_API_URL=https://goat-platform-745118591625.us-central1.run.app
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_OUTPUT=standalone
# Increase Node memory for Cloud Build
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# Cloud Run sets PORT (default 8080)
ENV PORT=8080
ENV HOSTNAME="0.0.0.0"
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
USER nextjs
EXPOSE 8080
CMD ["node", "server.js"]