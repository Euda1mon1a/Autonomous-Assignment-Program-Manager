***REMOVED*** Frontend Dockerfile for Residency Scheduler
***REMOVED*** Multi-stage build for minimal attack surface and optimized image size

***REMOVED*** =============================================================================
***REMOVED*** Build Stage - includes npm and build tools
***REMOVED*** =============================================================================
FROM node:22-slim AS builder
WORKDIR /app

***REMOVED*** Copy package files for dependency installation
COPY package.json package-lock.json* ./

***REMOVED*** Install dependencies
RUN npm ci --legacy-peer-deps && npm cache clean --force

***REMOVED*** Copy application source
COPY . .

***REMOVED*** Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

***REMOVED*** Build the application
RUN npm run build

***REMOVED*** =============================================================================
***REMOVED*** Runtime Stage - minimal production image
***REMOVED*** =============================================================================
FROM node:22-slim AS runtime
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

***REMOVED*** Copy public assets
COPY --from=builder /app/public ./public

***REMOVED*** Copy standalone build output (leverages Next.js output tracing for minimal size)
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

***REMOVED*** Expose port
EXPOSE 3000

***REMOVED*** Health check using Node (no wget in distroless)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/', (r) => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

***REMOVED*** Start the application
CMD ["node", "server.js"]
