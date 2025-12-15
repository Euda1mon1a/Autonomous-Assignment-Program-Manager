***REMOVED*** =============================================================================
***REMOVED*** Production Dockerfile for Residency Scheduler Frontend
***REMOVED*** =============================================================================
***REMOVED*** Multi-stage build with nginx for optimal production serving
***REMOVED*** Node 20 Alpine for building, nginx Alpine for serving
***REMOVED***
***REMOVED*** Build context should be the repository root:
***REMOVED***   docker build -f .docker/frontend.Dockerfile .
***REMOVED*** =============================================================================

***REMOVED*** -----------------------------------------------------------------------------
***REMOVED*** Stage 1: Dependencies - Install npm packages
***REMOVED*** -----------------------------------------------------------------------------
FROM node:20-alpine AS deps

***REMOVED*** Security: Check for vulnerabilities
RUN apk add --no-cache libc6-compat

WORKDIR /app

***REMOVED*** Copy package files for layer caching
COPY frontend/package.json frontend/package-lock.json* ./

***REMOVED*** Install all dependencies (including devDependencies for build)
RUN npm ci && npm cache clean --force

***REMOVED*** -----------------------------------------------------------------------------
***REMOVED*** Stage 2: Builder - Build the Next.js application
***REMOVED*** -----------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

***REMOVED*** Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .

***REMOVED*** Disable Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED=1

***REMOVED*** Build arguments for environment configuration
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

***REMOVED*** Build the application
RUN npm run build

***REMOVED*** -----------------------------------------------------------------------------
***REMOVED*** Stage 3: Production - Nginx serving static assets
***REMOVED*** -----------------------------------------------------------------------------
FROM nginx:1.25-alpine AS production

***REMOVED*** Labels for container identification
LABEL org.opencontainers.image.title="Residency Scheduler Frontend" \
    org.opencontainers.image.description="Next.js frontend served via nginx" \
    org.opencontainers.image.vendor="Residency Scheduler" \
    org.opencontainers.image.version="1.0.0" \
    maintainer="devops@residency-scheduler.local"

***REMOVED*** Install curl for health checks
RUN apk add --no-cache curl

***REMOVED*** Remove default nginx configuration
RUN rm -rf /etc/nginx/conf.d/default.conf /usr/share/nginx/html/*

***REMOVED*** Copy custom nginx configuration (from build context root)
COPY .docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY .docker/nginx/default.conf /etc/nginx/conf.d/default.conf

***REMOVED*** Copy Next.js standalone build output
COPY --from=builder /app/.next/standalone /usr/share/nginx/html
COPY --from=builder /app/.next/static /usr/share/nginx/html/.next/static
COPY --from=builder /app/public /usr/share/nginx/html/public

***REMOVED*** Create nginx user directories with proper permissions
RUN mkdir -p /var/cache/nginx /var/run/nginx && \
    chown -R nginx:nginx /var/cache/nginx /var/run/nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

***REMOVED*** Security: Remove unnecessary nginx modules
RUN rm -rf /etc/nginx/modules-available /etc/nginx/modules-enabled 2>/dev/null || true

***REMOVED*** Security hardening
RUN chmod 644 /etc/nginx/nginx.conf && \
    chmod 644 /etc/nginx/conf.d/*.conf

***REMOVED*** Switch to non-root user
USER nginx

***REMOVED*** Expose port
EXPOSE 80

***REMOVED*** Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

***REMOVED*** Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
