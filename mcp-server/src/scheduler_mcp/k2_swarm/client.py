"""Moonshot API client for K2.5 Agent Swarm."""

import json
import logging
import os
import time
import uuid
from pathlib import Path

import httpx

from .models import FilePatch, K2SwarmOutput

logger = logging.getLogger(__name__)

MAX_CONTEXT_SIZE = int(os.environ.get("K2_SWARM_MAX_CONTEXT_SIZE", "100000"))


class MoonshotAPIClient:
    """Client for Moonshot K2.5 API."""

    def __init__(self):
        self.api_key = os.environ.get("MOONSHOT_API_KEY", "")
        self.base_url = "https://api.moonshot.cn/v1"
        self._results: dict[str, K2SwarmOutput | None] = {}
        self._statuses: dict[str, str] = {}
        self._errors: dict[str, str] = {}

    def _load_context_files(self, filepaths: list[str]) -> str:
        """Load file contents as context, respecting size limit."""
        parts = []
        total = 0
        for fp in filepaths:
            path = Path(fp)
            if not path.exists():
                logger.warning(f"Context file not found: {fp}")
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                if total + len(content) > MAX_CONTEXT_SIZE:
                    logger.warning(
                        f"Context size limit reached at {fp}, skipping remaining"
                    )
                    break
                parts.append(f"### {fp}\n```\n{content}\n```")
                total += len(content)
            except Exception as e:
                logger.warning(f"Failed to read {fp}: {e}")
        return "\n\n".join(parts)

    async def spawn_task(
        self,
        task: str,
        mode: str = "agent_swarm",
        context_files: list[str] | None = None,
        max_tokens: int = 32000,
        output_format: str = "patches",
    ) -> str:
        """Spawn a K2.5 swarm task.

        Returns:
            task_id for polling
        """
        if not self.api_key:
            raise ValueError(
                "MOONSHOT_API_KEY not set. Get one from platform.moonshot.ai"
            )

        task_id = str(uuid.uuid4())[:8]

        # Build context
        context = ""
        if context_files:
            context = self._load_context_files(context_files)

        format_instruction = {
            "patches": (
                "Return results as unified diff patches. "
                "Format each change as:\n"
                "--- a/filepath\n+++ b/filepath\n@@ ... @@\n-old\n+new"
            ),
            "files": "Return complete file contents for each modified file.",
            "analysis": "Return a detailed text analysis of the codebase.",
        }.get(output_format, "Return results as patches.")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a code analysis and modification agent. "
                    f"{format_instruction}\n"
                    "Be precise and only modify what is needed."
                ),
            },
        ]

        if context:
            messages.append(
                {"role": "user", "content": f"Context files:\n\n{context}"}
            )

        messages.append({"role": "user", "content": task})

        self._statuses[task_id] = "running"
        self._results[task_id] = None
        self._errors[task_id] = ""

        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "kimi-k2.5",
                        "messages": messages,
                        "mode": mode,
                        "max_tokens": max_tokens,
                    },
                    timeout=300.0,
                )
                response.raise_for_status()
                data = response.json()

            elapsed = time.time() - start
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})

            self._results[task_id] = K2SwarmOutput(
                analysis=content,
                patches=self._extract_patches(content) if output_format == "patches" else None,
                tool_calls=usage.get("total_tokens", 0),
                agents_used=100 if mode == "agent_swarm" else 1,
                execution_time_seconds=elapsed,
            )
            self._statuses[task_id] = "completed"
            logger.info(
                f"K2.5 swarm task {task_id} completed in {elapsed:.1f}s "
                f"({usage.get('total_tokens', 0)} tokens)"
            )

        except Exception as e:
            self._statuses[task_id] = "failed"
            self._errors[task_id] = str(e)
            logger.error(f"K2.5 swarm task {task_id} failed: {e}")

        return task_id

    def get_status(self, task_id: str) -> str:
        return self._statuses.get(task_id, "unknown")

    def get_result(self, task_id: str) -> K2SwarmOutput | None:
        return self._results.get(task_id)

    def get_error(self, task_id: str) -> str:
        return self._errors.get(task_id, "")

    @staticmethod
    def _extract_patches(content: str) -> list[FilePatch]:
        """Extract unified diff patches from LLM output."""
        patches = []
        lines = content.split("\n")
        current_filepath = ""
        current_diff_lines: list[str] = []

        for line in lines:
            if line.startswith("--- a/"):
                if current_filepath and current_diff_lines:
                    patches.append(
                        FilePatch(
                            filepath=current_filepath,
                            diff="\n".join(current_diff_lines),
                        )
                    )
                current_filepath = line[6:]
                current_diff_lines = [line]
            elif line.startswith("+++ b/"):
                current_filepath = line[6:]
                current_diff_lines.append(line)
            elif current_diff_lines and (
                line.startswith("@@")
                or line.startswith("+")
                or line.startswith("-")
                or line.startswith(" ")
            ):
                current_diff_lines.append(line)

        if current_filepath and current_diff_lines:
            patches.append(
                FilePatch(
                    filepath=current_filepath,
                    diff="\n".join(current_diff_lines),
                )
            )

        return patches


# Singleton
_client: MoonshotAPIClient | None = None


def get_moonshot_client() -> MoonshotAPIClient:
    global _client
    if _client is None:
        _client = MoonshotAPIClient()
    return _client
