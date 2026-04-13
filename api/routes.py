"""
FastAPI routes for LogLense CI/CD analyzer.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from jenkins.client import jenkins_client
from analyzer.llm_client import llm_analyzer
from utils.log_parser import parse_console_log

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["loglense"])


# ------------------------------------------------------------------
# Response models
# ------------------------------------------------------------------

class BuildSummaryResponse(BaseModel):
    job_name: str
    build_number: int
    result: str
    duration_ms: int
    url: str
    causes: list[str]
    culprits: list[str]


class DirectAnalyseRequest(BaseModel):
    log: str
    job_name: str = "test-job"
    build_number: int = 0
    result: str = "FAILURE"


class AnalysisResponse(BaseModel):
    job_name: str
    build_number: int
    result: str
    analysis: str
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int


class QuickSummaryResponse(BaseModel):
    job_name: str
    build_number: int
    result: str
    summary: str


class TrendResponse(BaseModel):
    job_name: str
    analysis: str


class FlakynessResponse(BaseModel):
    job_name: str
    analysis: str


class CompareResponse(BaseModel):
    job_name: str
    build_a: int
    build_b: int
    analysis: str


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.get("/jobs", summary="List all Jenkins jobs")
async def list_jobs():
    """Return all top-level Jenkins jobs with health info."""
    try:
        jobs = await jenkins_client.list_jobs()
        return [j.__dict__ for j in jobs]
    except Exception as exc:
        logger.exception("Failed to list jobs")
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/jobs/{job_name}/builds/{build_number}", response_model=BuildSummaryResponse, summary="Get build metadata")
async def get_build(job_name: str, build_number: str = "lastBuild"):
    """Fetch metadata for a build without triggering LLM analysis."""
    try:
        build = await jenkins_client.get_build_info(job_name, build_number)
        return BuildSummaryResponse(**build.__dict__)
    except Exception as exc:
        logger.exception("Failed to get build %s/%s", job_name, build_number)
        raise HTTPException(status_code=502, detail=str(exc))


@router.get(
    "/jobs/{job_name}/builds/{build_number}/analyse",
    response_model=AnalysisResponse,
    summary="Full LLM failure analysis",
)
async def analyse_build(
    job_name: str,
    build_number: str = "lastBuild",
    use_condensed: bool = Query(True, description="Pre-parse log to reduce LLM tokens"),
):
    """
    Fetch build + console log from Jenkins, then run full LLM failure analysis.
    Returns structured Markdown with root cause, fix steps, and prevention tips.
    """
    try:
        build = await jenkins_client.get_build_with_log(job_name, build_number)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Jenkins error: {exc}")

    if use_condensed and build.console_log:
        parsed = parse_console_log(build.console_log)
        build.console_log = parsed.condensed

    try:
        result = llm_analyzer.analyse_failure(build)
    except Exception as exc:
        logger.exception("LLM analysis failed")
        raise HTTPException(status_code=500, detail=f"LLM error: {exc}")

    return AnalysisResponse(
        job_name=result.job_name,
        build_number=result.build_number,
        result=result.result,
        analysis=result.analysis,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        cached_tokens=result.cached_tokens,
    )


@router.get(
    "/jobs/{job_name}/builds/{build_number}/quick-summary",
    response_model=QuickSummaryResponse,
    summary="Quick 5-line triage summary",
)
async def quick_summary(job_name: str, build_number: str = "lastBuild"):
    """Fast, cheap triage — 5-line summary of what broke and how to fix it."""
    try:
        build = await jenkins_client.get_build_with_log(job_name, build_number)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Jenkins error: {exc}")

    try:
        result = llm_analyzer.quick_summary(build)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM error: {exc}")

    return QuickSummaryResponse(
        job_name=result.job_name,
        build_number=result.build_number,
        result=result.result,
        summary=result.analysis,
    )


@router.get(
    "/jobs/{job_name}/trend",
    response_model=TrendResponse,
    summary="Build trend and health analysis",
)
async def build_trend(
    job_name: str,
    last_n: int = Query(10, ge=2, le=50, description="Number of recent builds to analyse"),
):
    """Analyse build health trend across the last N builds."""
    try:
        builds = await jenkins_client.get_failed_builds(job_name, last_n=last_n)
        if not builds:
            return TrendResponse(job_name=job_name, analysis="No failed builds found in recent history.")
        analysis = llm_analyzer.analyse_build_trend(job_name, builds)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return TrendResponse(job_name=job_name, analysis=analysis)


@router.get(
    "/jobs/{job_name}/flaky-tests",
    response_model=FlakynessResponse,
    summary="Detect flaky tests across recent builds",
)
async def detect_flaky_tests(
    job_name: str,
    last_n: int = Query(5, ge=2, le=20),
):
    """Identify tests that fail intermittently across multiple builds."""
    try:
        builds = await jenkins_client.get_failed_builds(job_name, last_n=last_n)
        for b in builds:
            b.console_log = await jenkins_client.get_console_log(job_name, b.build_number)
        analysis = llm_analyzer.detect_flaky_tests(job_name, builds)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return FlakynessResponse(job_name=job_name, analysis=analysis)


@router.get(
    "/jobs/{job_name}/compare",
    response_model=CompareResponse,
    summary="Compare two builds side by side",
)
async def compare_builds(
    job_name: str,
    build_a: int = Query(..., description="First build number"),
    build_b: int = Query(..., description="Second build number"),
):
    """Compare two builds and explain what changed / what regressed."""
    try:
        b_a = await jenkins_client.get_build_with_log(job_name, build_a)
        b_b = await jenkins_client.get_build_with_log(job_name, build_b)
        analysis = llm_analyzer.compare_builds(b_a, b_b)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return CompareResponse(
        job_name=job_name,
        build_a=build_a,
        build_b=build_b,
        analysis=analysis,
    )


@router.post(
    "/analyse-log",
    response_model=AnalysisResponse,
    summary="Analyse a raw log directly (no Jenkins required)",
)
async def analyse_raw_log(body: DirectAnalyseRequest):
    """
    Paste any build log and get an LLM analysis instantly.
    Useful for testing without a live Jenkins connection.
    """
    from jenkins.client import BuildInfo
    build = BuildInfo(
        job_name=body.job_name,
        build_number=body.build_number,
        result=body.result,
        duration_ms=0,
        timestamp=0,
        url="",
        console_log=body.log,
    )
    parsed = parse_console_log(body.log)
    build.console_log = parsed.condensed
    try:
        result = llm_analyzer.analyse_failure(build)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM error: {exc}")
    return AnalysisResponse(
        job_name=result.job_name,
        build_number=result.build_number,
        result=result.result,
        analysis=result.analysis,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        cached_tokens=result.cached_tokens,
    )
