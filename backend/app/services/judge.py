"""Judge0 integration. It is deliberately gated behind an explicit secure-deployment flag."""
import httpx

from app.core.config import settings


class JudgeUnavailable(RuntimeError):
    pass


async def execute_python(source_code: str, stdin: str = "") -> dict:
    if not settings.judge0_base_url or not settings.judge0_secure_deployment_confirmed:
        raise JudgeUnavailable(
            "Code execution is disabled. Configure a hardened Judge0 deployment and set "
            "JUDGE0_SECURE_DEPLOYMENT_CONFIRMED=true after verifying its isolation settings."
        )

    headers = {"Content-Type": "application/json"}
    if settings.judge0_api_key:
        headers["X-Auth-Token"] = settings.judge0_api_key
    payload = {
        "source_code": source_code,
        "language_id": settings.judge0_python_language_id,
        "stdin": stdin,
        "cpu_time_limit": 2,
        "wall_time_limit": 5,
        "memory_limit": 128000,
        "base64_encoded": False,
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        response = await client.post(
            f"{settings.judge0_base_url.rstrip('/')}/submissions",
            params={"base64_encoded": "false", "wait": "true"},
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

    status = (result.get("status") or {}).get("description", "Unknown")
    return {
        "status": status,
        "stdout": result.get("stdout") or "",
        "stderr": result.get("stderr") or result.get("compile_output") or "",
        "time": result.get("time"),
        "memory": result.get("memory"),
        "token": result.get("token"),
    }
