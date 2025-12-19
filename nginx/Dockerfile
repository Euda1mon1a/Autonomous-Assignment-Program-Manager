***REMOVED*** =============================================================================
***REMOVED*** Nginx Reverse Proxy Dockerfile
***REMOVED*** =============================================================================
***REMOVED*** Alpine-based image for minimal attack surface
***REMOVED*** =============================================================================

FROM nginx:1.27-alpine

***REMOVED*** Labels
LABEL maintainer="Residency Scheduler Team"
LABEL description="Nginx reverse proxy for Residency Scheduler"
LABEL version="1.0"

***REMOVED*** Create required directories and remove default config in single layer
RUN mkdir -p \
    /var/www/certbot \
    /var/www/html \
    /etc/nginx/ssl \
    /etc/nginx/snippets \
    /var/log/nginx \
    && rm -f /etc/nginx/conf.d/default.conf

***REMOVED*** Copy nginx configuration files
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/
COPY snippets/ /etc/nginx/snippets/

***REMOVED*** Copy SSL directory (may contain dhparam.pem)
COPY ssl/ /etc/nginx/ssl/

***REMOVED*** Set proper permissions
RUN chown -R nginx:nginx /var/cache/nginx \
    && chown -R nginx:nginx /var/log/nginx \
    && chown -R nginx:nginx /var/www \
    && chmod -R 755 /etc/nginx

***REMOVED*** Create error pages
RUN echo '<!DOCTYPE html><html><head><title>503 Service Unavailable</title></head><body><h1>Service Temporarily Unavailable</h1><p>Please try again later.</p></body></html>' > /usr/share/nginx/html/50x.html

***REMOVED*** Health check using nginx's built-in status (no curl in distroless)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD nginx -t 2>/dev/null || exit 1

***REMOVED*** Expose ports
EXPOSE 80 443

***REMOVED*** Use exec form for proper signal handling
CMD ["nginx", "-g", "daemon off;"]
