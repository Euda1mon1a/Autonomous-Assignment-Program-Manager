# =============================================================================
# Production Dockerfile for Residency Scheduler Frontend
# =============================================================================
# Multi-stage build with nginx for optimal production serving
# Node 20 Alpine for building, nginx Alpine for serving
#
# Build context should be the repository root:
#   docker build -f .docker/frontend.Dockerfile .
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Dependencies - Install npm packages
# -----------------------------------------------------------------------------
FROM node:20-alpine AS deps

# Security: Check for vulnerabilities
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files for layer caching
COPY frontend/package.json frontend/package-lock.json* ./

# Install all dependencies (including devDependencies for build)
RUN npm ci && npm cache clean --force

# -----------------------------------------------------------------------------
# Stage 2: Builder - Build the Next.js application
# -----------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .

# Disable Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED=1

# Build arguments for environment configuration
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 3: Production - Nginx serving static assets
# -----------------------------------------------------------------------------
FROM nginx:1.25-alpine AS production

# Labels for container identification
LABEL org.opencontainers.image.title="Residency Scheduler Frontend" \
    org.opencontainers.image.description="Next.js frontend served via nginx" \
    org.opencontainers.image.vendor="Residency Scheduler" \
    org.opencontainers.image.version="1.0.0" \
    maintainer="devops@residency-scheduler.local"

# Install curl for health checks
RUN apk add --no-cache curl

# Remove default nginx configuration
RUN rm -rf /etc/nginx/conf.d/default.conf /usr/share/nginx/html/*

# Copy custom nginx configuration (from build context root)
COPY .docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY .docker/nginx/default.conf /etc/nginx/conf.d/default.conf

# Copy Next.js standalone build output
COPY --from=builder /app/.next/standalone /usr/share/nginx/html
COPY --from=builder /app/.next/static /usr/share/nginx/html/.next/static
COPY --from=builder /app/public /usr/share/nginx/html/public

# Create nginx user directories with proper permissions
RUN mkdir -p /var/cache/nginx /var/run/nginx && \
    chown -R nginx:nginx /var/cache/nginx /var/run/nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# Security: Remove unnecessary nginx modules
RUN rm -rf /etc/nginx/modules-available /etc/nginx/modules-enabled 2>/dev/null || true

# Security hardening
RUN chmod 644 /etc/nginx/nginx.conf && \
    chmod 644 /etc/nginx/conf.d/*.conf

# Switch to non-root user
USER nginx

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
