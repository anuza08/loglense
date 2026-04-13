"""
Jenkins API client — fetches job info, build details, and console logs.
"""

import base64
import logging
from dataclasses import dataclass, field
from typing import Optional, Union

import httpx

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class BuildInfo:
    job_name: str
    build_number: int
    result: str          # SUCCESS | FAILURE | UNSTABLE | ABORTED | None (in progress)
    duration_ms: int
    timestamp: int
    url: str
    causes: list[str] = field(default_factory=list)
    culprits: list[str] = field(default_factory=list)
    console_log: str = ""


@dataclass
class JobInfo:
    name: str
    url: str
    last_build_number: Optional[int]
    last_success_number: Optional[int]
    last_failure_number: Optional[int]
    health_score: int


class JenkinsClient:
    """Thin async wrapper around the Jenkins REST API."""

    def __init__(self):
        self.base_url = settings.jenkins_url.rstrip("/")
        credentials = f"{settings.jenkins_user}:{settings.jenkins_token}"
        token = base64.b64encode(credentials.encode()).decode()
        self._headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self._headers)
            resp.raise_for_status()
            return resp.json()

    async def _get_text(self, path: str) -> str:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url, headers=self._headers)
            resp.raise_for_status()
            return resp.text

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_jobs(self) -> list[JobInfo]:
        """Return all top-level jobs."""
        data = await self._get("/api/json?tree=jobs[name,url,healthReport[score],lastBuild[number],lastSuccessfulBuild[number],lastFailedBuild[number]]")
        jobs = []
        for j in data.get("jobs", []):
            health = j.get("healthReport", [])
            score = health[0].get("score", 0) if health else 0
            jobs.append(JobInfo(
                name=j["name"],
                url=j["url"],
                last_build_number=j.get("lastBuild", {}).get("number") if j.get("lastBuild") else None,
                last_success_number=j.get("lastSuccessfulBuild", {}).get("number") if j.get("lastSuccessfulBuild") else None,
                last_failure_number=j.get("lastFailedBuild", {}).get("number") if j.get("lastFailedBuild") else None,
                health_score=score,
            ))
        return jobs

    async def get_build_info(self, job_name: str, build_number: Union[int, str] = "lastBuild") -> BuildInfo:
        """Fetch metadata for a specific build (or the latest if build_number='lastBuild')."""
        path = f"/job/{job_name}/{build_number}/api/json?tree=number,result,duration,timestamp,url,causes[shortDescription],culprits[fullName]"
        data = await self._get(path)
        causes = [c.get("shortDescription", "") for c in data.get("causes", [])]
        culprits = [c.get("fullName", "") for c in data.get("culprits", [])]
        return BuildInfo(
            job_name=job_name,
            build_number=data["number"],
            result=data.get("result") or "IN_PROGRESS",
            duration_ms=data.get("duration", 0),
            timestamp=data.get("timestamp", 0),
            url=data.get("url", ""),
            causes=causes,
            culprits=culprits,
        )

    async def get_console_log(self, job_name: str, build_number: Union[int, str] = "lastBuild", max_chars: int = 50_000) -> str:
        """Fetch raw console output, truncated to max_chars from the tail."""
        path = f"/job/{job_name}/{build_number}/consoleText"
        try:
            text = await self._get_text(path)
            # Keep only the last max_chars so the LLM context stays manageable
            if len(text) > max_chars:
                text = "...[truncated]...\n" + text[-max_chars:]
            return text
        except httpx.HTTPStatusError as exc:
            logger.warning("Could not fetch console log for %s #%s: %s", job_name, build_number, exc)
            return ""

    async def get_failed_builds(self, job_name: str, last_n: int = 5) -> list[BuildInfo]:
        """Return up to last_n failed builds for a job."""
        path = f"/job/{job_name}/api/json?tree=builds[number,result,duration,timestamp,url]{{0,{last_n * 3}}}"
        data = await self._get(path)
        failed = []
        for b in data.get("builds", []):
            if b.get("result") == "FAILURE":
                failed.append(BuildInfo(
                    job_name=job_name,
                    build_number=b["number"],
                    result=b["result"],
                    duration_ms=b.get("duration", 0),
                    timestamp=b.get("timestamp", 0),
                    url=b.get("url", ""),
                ))
                if len(failed) >= last_n:
                    break
        return failed

    async def get_build_with_log(self, job_name: str, build_number: Union[int, str] = "lastBuild") -> BuildInfo:
        """Convenience method: fetch build info + console log in one call."""
        build = await self.get_build_info(job_name, build_number)
        build.console_log = await self.get_console_log(job_name, build_number)
        return build


jenkins_client = JenkinsClient()
