***REMOVED*** Claude Code Slack Bot
FROM node:20-slim

***REMOVED*** Install dependencies for Claude Code CLI
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

***REMOVED*** Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

***REMOVED*** Create app directory
WORKDIR /app/bot

***REMOVED*** Copy package files
COPY package*.json ./
COPY tsconfig.json ./

***REMOVED*** Install dependencies
RUN npm install

***REMOVED*** Copy source
COPY src ./src

***REMOVED*** Build TypeScript
RUN npm run build

***REMOVED*** Create workspace mount point
RUN mkdir -p /app/workspace

***REMOVED*** Default environment
ENV NODE_ENV=production
ENV CLAUDE_WORKING_DIR=/app/workspace

***REMOVED*** Start the bot
CMD ["npm", "start"]
