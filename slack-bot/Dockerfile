# Claude Code Slack Bot
FROM node:20-slim

# Install dependencies for Claude Code CLI
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Create app directory
WORKDIR /app/bot

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm install

# Copy source
COPY src ./src

# Build TypeScript
RUN npm run build

# Create workspace mount point
RUN mkdir -p /app/workspace

# Default environment
ENV NODE_ENV=production
ENV CLAUDE_WORKING_DIR=/app/workspace

# Start the bot
CMD ["npm", "start"]
