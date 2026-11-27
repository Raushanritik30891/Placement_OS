"""Judge0 adapter boundary.

Do not replace this with local eval/exec. Configure a hardened Judge0 service
before accepting untrusted submissions.
"""
import httpx

from app.core.config import settings


class JudgeUnavailable(RuntimeError):
    pass


async def submit_to_judge(source_code: str, language_id: int, stdin: str = "") -> dict:
    if not settings.judge0_base_url:
        raise JudgeUnavailable("Judge0 is not configured")

    headers = {"Content-Type": "application/json"}
    if settings.judge0_api_key:
        headers["X-Auth-Token"] = settings.judge0_api_key

    payload = {
        "source_code": source_code,
        "language_id": language_id,
        "stdin": stdin,
        "base64_encoded": False,
        "wait": False,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            f"{settings.judge0_base_url.rstrip('/')}/submissions",
            params={"base64_encoded": "false", "wait": "false"},
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()
