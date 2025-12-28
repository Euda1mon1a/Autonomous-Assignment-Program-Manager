import { App, LogLevel } from "@slack/bolt";
import { spawn } from "child_process";
import { config } from "dotenv";

config();

const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  appToken: process.env.SLACK_APP_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET,
  socketMode: true,
  logLevel: LogLevel.INFO,
});

// Session state per channel/thread
const sessions = new Map<string, { cwd: string }>();

function getSessionKey(channel: string, thread_ts?: string): string {
  return thread_ts ? `${channel}:${thread_ts}` : channel;
}

// Handle direct messages and mentions
app.event("app_mention", async ({ event, say }) => {
  const text = event.text.replace(/<@[^>]+>/g, "").trim();
  await handleMessage(text, event.channel, event.ts, say);
});

app.event("message", async ({ event, say }) => {
  // Only respond to DMs
  if (event.channel_type !== "im") return;
  if ("bot_id" in event) return; // Ignore bot messages

  const text = "text" in event ? event.text || "" : "";
  const thread_ts = "thread_ts" in event ? event.thread_ts : undefined;
  await handleMessage(text, event.channel, thread_ts, say);
});

async function handleMessage(
  text: string,
  channel: string,
  thread_ts: string | undefined,
  say: Function
) {
  const sessionKey = getSessionKey(channel, thread_ts);

  // Handle cwd command
  if (text.startsWith("cwd ")) {
    const newCwd = text.slice(4).trim();
    sessions.set(sessionKey, { cwd: newCwd });
    await say({
      text: `Working directory set to: \`${newCwd}\``,
      thread_ts,
    });
    return;
  }

  // Handle status command
  if (text === "status") {
    const session = sessions.get(sessionKey);
    await say({
      text: session
        ? `Current working directory: \`${session.cwd}\``
        : "No session. Use `cwd /path/to/project` to set working directory.",
      thread_ts,
    });
    return;
  }

  // Get session or use default
  const session = sessions.get(sessionKey) || {
    cwd: process.env.CLAUDE_WORKING_DIR || "/app/workspace",
  };

  // Send initial acknowledgment
  const ack = await say({
    text: `:robot_face: Processing: "${text.slice(0, 50)}${text.length > 50 ? "..." : ""}"`,
    thread_ts,
  });

  try {
    // Run Claude Code CLI
    const result = await runClaudeCode(text, session.cwd);

    // Post result
    await say({
      text: formatResponse(result),
      thread_ts,
      mrkdwn: true,
    });
  } catch (error) {
    await say({
      text: `:x: Error: ${error instanceof Error ? error.message : "Unknown error"}`,
      thread_ts,
    });
  }
}

async function runClaudeCode(prompt: string, cwd: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: string[] = [];

    // Use claude CLI in print mode for non-interactive operation
    const proc = spawn(
      "claude",
      [
        "-p", prompt,
        "--output-format", "text",
        "--allowedTools", "Bash(*)", "Edit", "Write", "Read", "Glob", "Grep",
      ],
      {
        cwd,
        env: {
          ...process.env,
          ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
        },
        stdio: ["pipe", "pipe", "pipe"],
      }
    );

    proc.stdout.on("data", (data) => {
      chunks.push(data.toString());
    });

    proc.stderr.on("data", (data) => {
      console.error(`stderr: ${data}`);
    });

    proc.on("close", (code) => {
      if (code === 0) {
        resolve(chunks.join(""));
      } else {
        reject(new Error(`Claude exited with code ${code}`));
      }
    });

    proc.on("error", (err) => {
      reject(err);
    });

    // Timeout after 10 minutes
    setTimeout(() => {
      proc.kill();
      reject(new Error("Timeout: Claude took too long"));
    }, 600000);
  });
}

function formatResponse(text: string): string {
  // Truncate if too long for Slack (4000 char limit)
  const MAX_LENGTH = 3900;
  if (text.length > MAX_LENGTH) {
    return text.slice(0, MAX_LENGTH) + "\n\n_...truncated_";
  }
  return text;
}

// Start the app
(async () => {
  await app.start();
  console.log("Claude Code Slack Bot is running!");
  console.log(`Default workspace: ${process.env.CLAUDE_WORKING_DIR || "/app/workspace"}`);
})();
