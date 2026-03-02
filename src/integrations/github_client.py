"""
Agentic NetOps — GitHub Integration Client
Commits generated Ansible playbooks to a GitHub repository.
"""

from __future__ import annotations

from typing import Any

from github import Github, GithubException

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GitHubClient:
    """
    GitHub client for committing generated playbooks.

    All authentication via GITHUB_TOKEN from environment.
    Credentials are read lazily at method call time, not at init.
    """

    def __init__(self) -> None:
        pass

    @property
    def github(self) -> Github:
        return Github(settings.github_token)

    @property
    def repo_name(self) -> str:
        return f"{settings.github_repo_owner}/{settings.github_repo_name}"

    async def commit_file(
        self,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> dict[str, Any] | None:
        """
        Commit a file to the GitHub repository.

        If the file already exists, it will be updated. Otherwise, it will be created.

        Args:
            path: File path within the repository (e.g., "playbooks/chg001_playbook.yml").
            content: File content to commit.
            message: Commit message.
            branch: Target branch (default: "main").

        Returns:
            Commit info dict with 'sha' and 'url', or None on failure.
        """
        try:
            repo = self.github.get_repo(self.repo_name)

            # Check if file already exists (update vs create)
            try:
                existing = repo.get_contents(path, ref=branch)
                result = repo.update_file(
                    path=path,
                    message=message,
                    content=content,
                    sha=existing.sha,
                    branch=branch,
                )
                logger.info(
                    "File updated in GitHub",
                    extra={"action": "update", "path": path},
                )
            except GithubException:
                # File doesn't exist — create it
                result = repo.create_file(
                    path=path,
                    message=message,
                    content=content,
                    branch=branch,
                )
                logger.info(
                    "File created in GitHub",
                    extra={"action": "create", "path": path},
                )

            return {
                "sha": result["commit"].sha,
                "url": result["commit"].html_url,
            }

        except GithubException as e:
            logger.error("GitHub API error", extra={"error": str(e), "path": path})
            return None
