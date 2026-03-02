"""
Agentic NetOps — Ansible AWX REST API Client
Triggers job templates and polls for job completion.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AWXClient:
    """
    Client for Ansible AWX REST API.

    Used to trigger pre-check, execution, post-check, and rollback job templates.
    Credentials are read lazily at method call time, not at init.
    """

    def __init__(self) -> None:
        self.headers = {"Content-Type": "application/json"}

    @property
    def base_url(self) -> str:
        return settings.awx_host.rstrip("/")

    @property
    def auth(self) -> tuple[str, str]:
        return (settings.awx_username, settings.awx_password)

    @property
    def verify_ssl(self) -> bool:
        return settings.awx_verify_ssl

    async def launch_job(
        self,
        template_name: str,
        extra_vars: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Launch an AWX job template by name.

        Args:
            template_name: Name of the AWX job template.
            extra_vars: Additional variables to pass to the template.

        Returns:
            Job info dict with 'id' and 'status', or None on failure.
        """
        template_id = await self._get_template_id(template_name)
        if not template_id:
            logger.error("Job template not found", extra={"action": template_name})
            return None

        url = f"{self.base_url}/api/v2/job_templates/{template_id}/launch/"
        payload = {}
        if extra_vars:
            payload["extra_vars"] = extra_vars

        try:
            async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                response = await client.post(
                    url,
                    json=payload,
                    auth=self.auth,
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                job_data = response.json()
                job_info = {
                    "id": job_data["id"],
                    "status": job_data.get("status", "pending"),
                    "url": f"{self.base_url}/#/jobs/playbook/{job_data['id']}",
                }

                logger.info(
                    "AWX job launched",
                    extra={"action": template_name, "status": job_info["status"]},
                )
                return job_info
        except httpx.HTTPError as e:
            logger.error("AWX launch error", extra={"error": str(e)})
            return None

    async def wait_for_job(
        self,
        job_id: int,
        poll_interval: float = 5.0,
        timeout: float = 600.0,
    ) -> dict[str, Any]:
        """
        Poll an AWX job until it completes or times out.

        Args:
            job_id: The AWX job ID to monitor.
            poll_interval: Seconds between polls (default: 5).
            timeout: Maximum wait time in seconds (default: 600).

        Returns:
            Job result dict with 'status', 'stdout', and parsed check results.
        """
        url = f"{self.base_url}/api/v2/jobs/{job_id}/"
        elapsed = 0.0

        while elapsed < timeout:
            try:
                async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                    response = await client.get(
                        url, auth=self.auth, headers=self.headers, timeout=30.0
                    )
                    response.raise_for_status()
                    job_data = response.json()
                    status = job_data.get("status", "")

                    if status in ("successful", "failed", "error", "canceled"):
                        # Fetch stdout for result parsing
                        stdout = await self._get_job_stdout(job_id)
                        result = {
                            "status": status,
                            "stdout": stdout,
                            "finished": job_data.get("finished"),
                        }

                        # Parse check results from stdout
                        result.update(self._parse_check_results(stdout))

                        logger.info(
                            "AWX job completed",
                            extra={"status": status},
                        )
                        return result

            except httpx.HTTPError as e:
                logger.warning("AWX poll error", extra={"error": str(e)})

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        logger.error("AWX job timed out", extra={"status": "timeout"})
        return {"status": "timeout", "stdout": "", "error": "Job timed out"}

    async def _get_template_id(self, template_name: str) -> int | None:
        """Resolve a job template name to its AWX ID."""
        url = f"{self.base_url}/api/v2/job_templates/"
        params = {"name": template_name}

        try:
            async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                response = await client.get(
                    url, params=params, auth=self.auth, headers=self.headers, timeout=30.0
                )
                response.raise_for_status()
                results = response.json().get("results", [])
                if results:
                    return results[0]["id"]
                return None
        except httpx.HTTPError:
            return None

    async def _get_job_stdout(self, job_id: int) -> str:
        """Fetch the stdout output of a completed AWX job."""
        url = f"{self.base_url}/api/v2/jobs/{job_id}/stdout/"
        params = {"format": "txt"}

        try:
            async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                response = await client.get(
                    url, params=params, auth=self.auth, timeout=30.0
                )
                response.raise_for_status()
                return response.text
        except httpx.HTTPError:
            return ""

    def _parse_check_results(self, stdout: str) -> dict[str, bool]:
        """
        Parse pre/post-check results from AWX job stdout.

        Looks for markers like 'ICMP_PING: OK' and 'SSH_TEST: OK'
        that the check playbooks are expected to output.
        """
        results: dict[str, bool] = {}
        stdout_lower = stdout.lower()

        # ICMP ping check
        if "icmp_ping: ok" in stdout_lower or "ping_result: success" in stdout_lower:
            results["icmp_ping"] = True
        elif "icmp_ping:" in stdout_lower or "ping_result:" in stdout_lower:
            results["icmp_ping"] = False

        # SSH connectivity check
        if "ssh_test: ok" in stdout_lower or "ssh_result: success" in stdout_lower:
            results["ssh_test"] = True
        elif "ssh_test:" in stdout_lower or "ssh_result:" in stdout_lower:
            results["ssh_test"] = False

        # TCP port check (post-validation)
        if "tcp_port_check: ok" in stdout_lower or "port_result: success" in stdout_lower:
            results["tcp_port_check"] = True
        elif "tcp_port_check:" in stdout_lower or "port_result:" in stdout_lower:
            results["tcp_port_check"] = False

        return results
