import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from dotenv import load_dotenv


def find_failed_runs(state_dir: Path) -> list[Path]:
    """Scan the state directory for MAF runs that resulted in a failure or escalation."""
    failed_runs = []
    if not state_dir.exists():
        return failed_runs

    for run_dir in state_dir.iterdir():
        if not run_dir.is_dir():
            continue
        
        status_file = run_dir / "status.json"
        if status_file.exists():
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("status") == "failed" or data.get("escalated", False):
                        failed_runs.append(run_dir)
            except Exception:
                pass
    return failed_runs


def build_improver_payload(run_dir: Path) -> dict:
    """Extract context from the failed run to send to Prompt Improver."""
    return {
        "run_id": run_dir.name,
        "original_prompt_file": str(run_dir / "prompt.txt"),
        "error_trace_file": str(run_dir / "error.log"),
    }


def trigger_prompt_improver(payload: dict, improver_path: Path):
    """Invoke the universal refiner with the failed context."""
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env", override=False)
    print(f"Triggering Prompt Improver for run {payload['run_id']}...")
    env = os.environ.copy()
    refiner_root = improver_path / "universal-refiner"
    cli_script = refiner_root / "scripts" / "operations" / "optimize-prompt.mjs"

    cmd = [
        "node",
        str(cli_script),
        "--prompt-file",
        payload["original_prompt_file"],
        "--context-file",
        payload["error_trace_file"],
        "--root-path",
        str(project_root),
        "--output-file",
        payload["original_prompt_file"],
        "--iterations",
        "2",
    ]
    
    try:
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, cwd=refiner_root, env=env, check=True)
        print("Prompt optimized successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Prompt Improver failed: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Agentic SDLC Auto Improver Loop")
    parser.add_argument("--state-dir", type=str, default="../state", help="Path to MAF state directory")
    parser.add_argument("--improver-dir", type=str, default="../../Promptimprover", help="Path to Prompt Improver repo")
    args = parser.parse_args()

    state_dir = Path(args.state_dir).resolve()
    improver_dir = Path(args.improver_dir).resolve()

    print(f"Scanning {state_dir} for failed runs...")
    failed_runs = find_failed_runs(state_dir)
    
    if not failed_runs:
        print("No failed runs detected. Agentic SDLC is healthy.")
        return

    print(f"Detected {len(failed_runs)} failed/escalated runs. Routing to Prompt Improver...")
    
    for run in failed_runs:
        payload = build_improver_payload(run)
        trigger_prompt_improver(payload, improver_dir)


if __name__ == "__main__":
    main()
