import tempfile  # to create a file on disk for semgrep_scan
import os
import sys
import json
import shutil
import subprocess
import contextlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, trace, set_tracing_disabled, OpenAIChatCompletionsModel

from context import SECURITY_RESEARCHER_INSTRUCTIONS, get_analysis_prompt, enhance_summary
from mcp_servers import create_semgrep_server

load_dotenv(override=True)

app = FastAPI(title="Cybersecurity Analyzer API")

# Configure CORS for development and production
cors_origins = [
    "http://localhost:3000",  # Local development
    "http://frontend:3000",  # Docker development
]

# In production, allow same-origin requests (static files served from same domain)
if os.getenv("ENVIRONMENT") == "production":
    cors_origins.append(
        "*"
    )  # Allow all origins in production since we serve frontend from same domain

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    code: str


class SecurityIssue(BaseModel):
    title: str = Field(description="Brief title of the security vulnerability")
    description: str = Field(
        description="Detailed description of the security issue and its potential impact"
    )
    code: str = Field(
        description="The specific vulnerable code snippet that demonstrates the issue"
    )
    fix: str = Field(description="Recommended code fix or mitigation strategy")
    cvss_score: float = Field(description="CVSS score from 0.0 to 10.0 representing severity")
    severity: str = Field(description="Severity level: critical, high, medium, or low")


class SecurityReport(BaseModel):
    summary: str = Field(description="Executive summary of the security analysis")
    issues: List[SecurityIssue] = Field(description="List of identified security vulnerabilities")


def validate_request(request: AnalyzeRequest) -> None:
    """Validate the analysis request."""
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="No code provided for analysis")


def check_api_keys() -> None:
    """Verify required API keys are configured."""
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not gemini_key and not openai_key:
        raise HTTPException(
            status_code=500,
            detail="No API key configured. Please set GEMINI_API_KEY or OPENAI_API_KEY in .env",
        )


def create_security_agent(semgrep_server=None) -> Agent:
    """Create and configure the security analysis agent."""
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    mcp_servers = [semgrep_server] if semgrep_server is not None else []

    # Detect Gemini if GEMINI_API_KEY is provided or OPENAI_API_KEY is a non-OpenAI key
    if gemini_key or (openai_key and not openai_key.startswith("sk-")):
        api_key = gemini_key if gemini_key else openai_key
        set_tracing_disabled(True)
        os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

        client = AsyncOpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key,
        )
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        model = OpenAIChatCompletionsModel(
            model=gemini_model,
            openai_client=client,
        )
        return Agent(
            name="Security Researcher",
            instructions=SECURITY_RESEARCHER_INSTRUCTIONS,
            model=model,
            mcp_servers=mcp_servers,
            output_type=SecurityReport,
        )

    return Agent(
        name="Security Researcher",
        instructions=SECURITY_RESEARCHER_INSTRUCTIONS,
        model="gpt-4.1-mini",
        mcp_servers=mcp_servers,
        output_type=SecurityReport,
    )


def format_semgrep_findings(raw_stdout: str) -> tuple[str, int]:
    """Parse Semgrep JSON output into structured findings and return count."""
    if not raw_stdout:
        return ("Semgrep static analysis was not available or produced no findings.", 0)
    try:
        data = json.loads(raw_stdout)
        results = data.get("results", [])
        if not results:
            return ("Semgrep static analysis ran successfully and identified 0 issues.", 0)

        findings = []
        for i, item in enumerate(results, 1):
            check_id = item.get("check_id", "Unknown rule")
            line = item.get("start", {}).get("line", "?")
            message = item.get("extra", {}).get("message", "Potential vulnerability detected.")
            severity = item.get("extra", {}).get("severity", "WARNING")
            lines_code = item.get("extra", {}).get("lines", "").strip()
            findings.append(
                f"Finding #{i}:\n"
                f"- Rule: {check_id}\n"
                f"- Line: {line}\n"
                f"- Severity: {severity}\n"
                f"- Description: {message}\n"
                f"- Code: {lines_code}"
            )
        summary_text = (
            f"Semgrep static analysis identified {len(results)} vulnerability(ies):\n\n"
            + "\n\n".join(findings)
        )
        return (summary_text, len(results))
    except Exception:
        return (f"Semgrep raw findings:\n{raw_stdout[:3000]}", 0)


def run_direct_semgrep_scan(temp_path: str) -> str:
    """Run semgrep directly via CLI to avoid multi-turn tool calling thought_signature incompatibility."""
    semgrep_cmd = "semgrep"
    if not shutil.which("semgrep"):
        venv_bin = os.path.dirname(sys.executable)
        candidates = [
            os.path.join(venv_bin, "semgrep.exe"),
            os.path.join(venv_bin, "semgrep"),
            "/root/.local/bin/semgrep",
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                semgrep_cmd = candidate
                break

    try:
        env = os.environ.copy()
        env["SEMGREP_APP_TOKEN"] = os.getenv("SEMGREP_APP_TOKEN", "")
        result = subprocess.run(
            [semgrep_cmd, "scan", "--config", "auto", "--json", temp_path],
            capture_output=True,
            text=True,
            timeout=90,
            env=env,
        )
        if result.stdout:
            return result.stdout
    except Exception as e:
        print(f"Semgrep direct scan notice: {e}")
    return ""


def get_gemini_analysis_prompt(code: str, semgrep_findings: str, semgrep_count: int) -> str:
    return f"""The application code to defensively audit and remediate is:

{code}

---
SEMGREP STATIC ANALYSIS RESULTS:
{semgrep_findings}
---

Your task as a defensive code security auditor:
1. Perform a defensive source code quality and security review to help developers fix defects, remediate bugs, and apply secure coding practices.
2. Review Semgrep's static analysis results above and include identified security issues (e.g. SQL injection, untrusted dynamic code execution, insecure configurations).
3. Conduct your own additional defensive review to identify any further bugs, edge cases, or architectural weaknesses that Semgrep might have missed.
4. In your summary, clearly state: "Semgrep found {semgrep_count} issues, and I identified X additional issues" (where X is the number of additional issues you found).
5. For each issue, provide:
   - title
   - detailed description and impact
   - the specific vulnerable code snippet
   - recommended defensive fix or mitigation code
   - CVSS score (0.0 to 10.0)
   - severity (critical, high, medium, or low)
6. Sort all issues in descending order of CVSS score."""


async def run_security_analysis(code: str) -> SecurityReport:
    """Execute the security analysis workflow."""
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    is_gemini = bool(gemini_key or (openai_key and not openai_key.startswith("sk-")))

    if is_gemini:
        # For Gemini, run Semgrep directly via CLI to avoid thought_signature mismatch in multi-turn tool calling
        agent = create_security_agent(semgrep_server=None)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp:
            temp.write(code)
            temp_path = temp.name
        try:
            raw_semgrep_output = run_direct_semgrep_scan(temp_path)
            semgrep_findings, semgrep_count = format_semgrep_findings(raw_semgrep_output)
            prompt = get_gemini_analysis_prompt(code, semgrep_findings, semgrep_count)
            result = await Runner.run(agent, input=prompt)
            sorted_report = result.final_output_as(SecurityReport)
            sorted_report.issues.sort(key=lambda issue: issue.cvss_score, reverse=True)
            return sorted_report
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    # For OpenAI, run standard MCP server workflow
    with trace("Security Researcher"):
        semgrep_context = None
        semgrep = None
        try:
            semgrep_context = create_semgrep_server()
            semgrep = await semgrep_context.__aenter__()
        except Exception as e:
            print(f"Notice: Semgrep MCP server could not be started ({e}). Proceeding with AI model analysis.")
            semgrep = None

        try:
            agent = create_security_agent(semgrep)
            with tempfile.NamedTemporaryFile(  # Creates a temporary file locally with the code
                mode="w", suffix=".py", delete=False
            ) as temp:
                temp.write(code)
                temp_path = temp.name
            try:
                result = await Runner.run(
                    agent, input=get_analysis_prompt(code, temp_path)
                )  # Sends code and path to the file
                # Changed the following two lines to sort by CVSS in descending order
                sorted_report = result.final_output_as(SecurityReport)
                sorted_report.issues.sort(key=lambda issue: issue.cvss_score, reverse=True)

                return sorted_report
            finally:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise
        finally:
            if semgrep_context and semgrep:
                try:
                    await semgrep_context.__aexit__(None, None, None)
                except Exception:
                    pass


def format_analysis_response(code: str, report: SecurityReport) -> SecurityReport:
    """Format the final analysis response."""
    enhanced_summary = enhance_summary(len(code), report.summary)
    return SecurityReport(summary=enhanced_summary, issues=report.issues)


@app.post("/api/analyze", response_model=SecurityReport)
async def analyze_code(request: AnalyzeRequest) -> SecurityReport:
    """
    Analyze Python code for security vulnerabilities using OpenAI Agents and Semgrep.

    This endpoint combines static analysis via Semgrep with AI-powered security analysis
    to provide comprehensive vulnerability detection and remediation guidance.
    """
    validate_request(request)
    check_api_keys()

    try:
        report = await run_security_analysis(request.code)
        return format_analysis_response(request.code, report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"message": "Cybersecurity Analyzer API"}


# Mount static files for frontend
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
