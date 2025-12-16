***REMOVED*** Frontend Dockerfile for Residency Scheduler
***REMOVED*** Node 22 LTS Alpine with multi-stage build for minimal production image

***REMOVED*** Base stage
FROM node:22-alpine AS base
RUN apk add --no-cache libc6-compat
WORKDIR /app

***REMOVED*** Dependencies stage - install only when needed
FROM base AS deps
COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps && npm cache clean --force

***REMOVED*** Builder stage - build the application
FROM base AS builder
WORKDIR /app

***REMOVED*** Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

***REMOVED*** Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

***REMOVED*** Build the application
RUN npm run build

***REMOVED*** Production stage - minimal runtime image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

***REMOVED*** Create non-root user for security
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

***REMOVED*** Copy public assets
COPY --from=builder /app/public ./public

***REMOVED*** Create .next directory and set permissions
RUN mkdir .next && chown nextjs:nodejs .next

***REMOVED*** Copy standalone build output (leverages Next.js output tracing for minimal size)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

***REMOVED*** Switch to non-root user
USER nextjs

***REMOVED*** Expose port
EXPOSE 3000

***REMOVED*** Set hostname to listen on all interfaces
ENV PORT=3000 \
    HOSTNAME="0.0.0.0"

***REMOVED*** Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

***REMOVED*** Start the application
CMD ["node", "server.js"]
