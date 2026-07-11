import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
import argparse
import os
import re
import shutil
import time
from pathlib import Path

from agent_framework import Message
from maf_starter.team_factory import build_repo_team
from maf_starter.config import load_settings
import logging

state_dir = Path("state").resolve()
state_dir.mkdir(parents=True, exist_ok=True)
log_file = state_dir / "daemon.log"

logger = logging.getLogger("autonomous_daemon")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(log_file, encoding="utf-8")
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

DEFAULT_POLL_INTERVAL_SECONDS = 5.0
DEFAULT_RETRY_DELAY_SECONDS = 15.0
PLANNER_COOLDOWN_SECONDS = 300.0

def log(msg: str):
    stream_encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    safe_msg = msg.encode(stream_encoding, errors="replace").decode(stream_encoding, errors="replace")
    logger.info(safe_msg)

# The auto-improver script we wrote earlier
from scripts.auto_improver_loop import trigger_prompt_improver, build_improver_payload


def _extract_pending_phase(roadmap_content: str) -> tuple[str, str, str] | None:
    match = re.search(r"- \[ \] \*\*Phase ([0-9.]+): (.*?)\*\* - (.*?)\n", roadmap_content)
    if not match:
        return None
    return match.group(1), match.group(2), match.group(3)


def _extract_pending_plan(roadmap_content: str) -> tuple[str, str] | None:
    match = re.search(r"^\s*-\s\[ \]\s([0-9]+-[0-9]+):\s(.+)$", roadmap_content, flags=re.MULTILINE)
    if not match:
        return None
    return match.group(1), match.group(2).strip()


def _build_phase_task(path: Path, *, phase_num: str, phase_title: str, phase_desc: str) -> None:
    path.write_text(
        f"# Phase {phase_num}: {phase_title}\n\n"
        f"Description: {phase_desc}\n\n"
        "Operate fully autonomously. Use the GSD and SDLC workflow end-to-end.\n"
        "Use specialist fan-out where it improves quality or speed, then converge on implementation and verification.\n"
        "Read `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, and relevant code before editing.\n"
        "Update roadmap and planning artifacts as part of the work when behavior changes.\n",
        encoding="utf-8",
    )


def _build_plan_task(path: Path, *, plan_id: str, plan_title: str) -> None:
    path.write_text(
        f"# Plan {plan_id}: {plan_title}\n\n"
        "Operate fully autonomously. Execute this plan item using the GSD + SDLC loop without waiting for human steering.\n"
        "Use research, architecture, security, and test specialist fan-out where useful before committing to the final implementation path.\n"
        "Read the relevant phase section in `.planning/ROADMAP.md` plus `.planning/PROJECT.md`, `.planning/STATE.md`, and live code.\n"
        "Implement, validate, self-heal on failure, and mark the plan complete in the roadmap when done.\n",
        encoding="utf-8",
    )


def _build_frontier_task(path: Path) -> None:
    path.write_text(
        "# Frontier Mode: Auto-Plan Next Phase\n\n"
        "No unchecked roadmap phases or plans remain.\n"
        "Act as an autonomous project manager and create the next best implementation phase.\n"
        "1. Use your read tools to read `.planning/PROJECT.md`, `.planning/STATE.md`, and `.planning/ROADMAP.md`.\n"
        "2. Identify the highest-leverage missing capability, reliability gap, or self-healing improvement.\n"
        "3. CRITICAL: You MUST use your file editing/writing tools to directly append the new roadmap phase to `.planning/ROADMAP.md`! Do not just output the text. Use active `[ ]` checkboxes, not `[?]`.\n"
        "4. Optimize for continuous autonomous execution with no human steering required.\n"
        "5. Favor GSD, SDLC, self-improvement, validation hardening, and specialist fan-out support.\n",
        encoding="utf-8",
    )


def _mark_roadmap_item_complete(roadmap_path: Path, *, file_name: str) -> str | None:
    if not roadmap_path.exists():
        return None
    content = roadmap_path.read_text(encoding="utf-8")
    updated = content
    item_label: str | None = None

    if file_name.startswith("gsd-plan-"):
        plan_id = file_name.removeprefix("gsd-plan-").removesuffix(".md")
        updated = updated.replace(f"- [ ] {plan_id}:", f"- [x] {plan_id}:")
        item_label = f"Plan {plan_id}"
    elif file_name.startswith("gsd-phase-"):
        phase_num = file_name.removeprefix("gsd-phase-").removesuffix(".md")
        updated = updated.replace(f"- [ ] **Phase {phase_num}:", f"- [x] **Phase {phase_num}:")
        item_label = f"Phase {phase_num}"

    if updated != content:
        roadmap_path.write_text(updated, encoding="utf-8")
    return item_label


async def process_inbox(inbox_dir: Path, completed_dir: Path, improver_dir: Path):
    """Scan inbox, process Markdown tasks, and self-heal on failure."""
    
    log(f"Polling {inbox_dir} for new steering instructions...")
    files = list(inbox_dir.glob("*.md"))
    
    # GSD Autonomous Bridge: If inbox is empty, pull the next phase from ROADMAP.md
    if not files:
        roadmap_path = Path(".planning/ROADMAP.md").resolve()
        if roadmap_path.exists():
            roadmap_content = roadmap_path.read_text(encoding="utf-8")
            
            # Check for circuit breaker [!]
            if "- [!] **Phase" in roadmap_content:
                log("⚠️ PIPELINE HALTED: A phase is blocked ([!]) in ROADMAP.md. Awaiting human intervention.")
                return

            pending_plan = _extract_pending_plan(roadmap_content)
            pending_phase = _extract_pending_phase(roadmap_content)

            if pending_plan is not None:
                plan_id, plan_title = pending_plan
                log(f"Found pending GSD plan {plan_id}: {plan_title}")
                new_task = inbox_dir / f"gsd-plan-{plan_id}.md"
                _build_plan_task(new_task, plan_id=plan_id, plan_title=plan_title)
                files = [new_task]
            elif pending_phase is not None:
                phase_num, phase_title, phase_desc = pending_phase
                log(f"Found pending GSD Phase {phase_num}: {phase_title}")
                new_task = inbox_dir / f"gsd-phase-{phase_num}.md"
                _build_phase_task(new_task, phase_num=phase_num, phase_title=phase_title, phase_desc=phase_desc)
                files = [new_task]
            else:
                failed_planner = completed_dir / "gsd-frontier-planner.md.failed"
                completed_planner = completed_dir / "gsd-frontier-planner.md"
                if failed_planner.exists():
                    time_since_failure = time.time() - failed_planner.stat().st_mtime
                    if time_since_failure > PLANNER_COOLDOWN_SECONDS:
                        logging.info("AUTONOMOUS SELF-HEAL: Re-queueing failed planner for retry.")
                        failed_planner.rename(inbox_dir / "gsd-frontier-planner.md")
                        files = [inbox_dir / "gsd-frontier-planner.md"]
                    else:
                        logging.info(f"FRONTIER PAUSE: Auto-Planner failed. Cooling down for {int(PLANNER_COOLDOWN_SECONDS - time_since_failure)}s before auto-retry.")
                elif completed_planner.exists() and (time.time() - completed_planner.stat().st_mtime) < PLANNER_COOLDOWN_SECONDS:
                    log("FRONTIER PAUSE: Auto-Planner ran recently but roadmap was not updated. Cooling down for 5 minutes.")
                else:
                    log("FRONTIER MODE: No unchecked roadmap work remains. Triggering Auto-Planner to draft the next autonomous phase.")
                    planner_task = inbox_dir / "gsd-frontier-planner.md"
                    _build_frontier_task(planner_task)
                    files = [planner_task]

    
    for file_path in files:
        log(f"Found new steering file: {file_path.name}")
        with open(file_path, "r", encoding="utf-8") as f:
            instruction = f.read()

        # Build MAF team
        settings = load_settings()
        team = build_repo_team(settings)
        
        # We enforce FULL_AUTO override here so approval_policy doesn't block
        os.environ["MAF_FULL_AUTO"] = "true"
        
        max_retries = 3
        attempt = 0
        success = False

        while attempt < max_retries and not success:
            attempt += 1
            log(f"--- Attempt {attempt} for {file_path.name} ---")
            
            try:
                # Intercept gsd-frontier-planner to handle it explicitly without relying on 3B tool calling
                if "gsd-frontier-planner.md" in file_path.name:
                    log("Running specialized Frontier Planner (bypassing MAF tool requirements)...")
                    roadmap_path = Path(".planning/ROADMAP.md").resolve()
                    roadmap_content = roadmap_path.read_text(encoding="utf-8")
                    
                    import urllib.request
                    import json
                    
                    prompt = f"Here is the current ROADMAP.md:\n{roadmap_content}\n\n" \
                             "Create exactly one new phase (Phase 10 or whatever is next) with concrete plan items using active `[ ]` checkboxes.\n" \
                             "Identify the highest-leverage missing capability for continuous autonomous execution.\n" \
                             "Output ONLY the markdown for the new phase. Start your output with '### Phase '."
                             
                    req = urllib.request.Request(
                        "http://127.0.0.1:20128/v1/chat/completions",
                        headers={"Content-Type": "application/json"},
                        data=json.dumps({
                            "model": "openrouter/free",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.2
                        }).encode("utf-8")
                    )
                    
                    with urllib.request.urlopen(req) as response:
                        body = json.loads(response.read().decode("utf-8"))
                        phase_text = body["choices"][0]["message"]["content"].strip()
                    
                    if phase_text and "### Phase" in phase_text:
                        # Extract only the first phase if the model hallucinated multiple
                        parts = phase_text.split("### Phase ")
                        if len(parts) >= 2:
                            # parts[0] is empty or preamble, parts[-1] is the last phase generated
                            phase_text = "### Phase " + parts[-1].strip()
                            
                        # If the model hallucinated '## Progress' inside its output, strip it out to avoid duplication
                        if "## Progress" in phase_text:
                            phase_text = phase_text.split("## Progress")[0].strip()
                            
                        # Append it before '## Progress' or at the end
                        if "## Progress" in roadmap_content:
                            roadmap_content = roadmap_content.replace("## Progress", f"{phase_text}\n\n## Progress", 1)
                        else:
                            roadmap_content += f"\n\n{phase_text}\n"
                        roadmap_path.write_text(roadmap_content, encoding="utf-8")
                        log("Successfully appended new phase to ROADMAP.md!")
                        success = True
                    else:
                        raise ValueError(f"Model generated invalid phase text: {phase_text}")
                else:
                    # Run the standard MAF workflow
                    log(f"Executing MAF workflow with input: '{instruction[:50]}...'")
                    result = await team.run(message=instruction)
                    log("MAF workflow completed successfully.")
                    success = True
                
            except Exception as e:
                log(f"MAF workflow encountered an error: {e}")
                log("Self-healing triggered...")
                
                # We need to construct a payload for the improver.
                # In a real environment, we'd grab the run dir. Here we mock it via team's checkpoint dir.
                run_dir = team.artifact_layout.checkpoint_dir
                
                # Make sure the error is recorded for the refiner
                with open(run_dir / "error.log", "w", encoding="utf-8") as err_f:
                    err_f.write(str(e))
                with open(run_dir / "prompt.txt", "w", encoding="utf-8") as prompt_f:
                    prompt_f.write(instruction)
                
                payload = build_improver_payload(run_dir)
                
                # Trigger the Prompt Improver CLI
                trigger_prompt_improver(payload, improver_dir)
                
                log("Refiner finished. Reloading agents for retry in 5 seconds...")
                await asyncio.sleep(5)
                # Rebuild team with potentially updated instructions/prompts
                team = build_repo_team(settings)

        if success:
            dest = completed_dir / file_path.name
            shutil.move(file_path, dest)
            log(f"Task completed and moved to {dest}")
            
            if file_path.name.startswith(("gsd-phase-", "gsd-plan-")):
                try:
                    roadmap_path = Path(".planning/ROADMAP.md").resolve()
                    item_label = _mark_roadmap_item_complete(roadmap_path, file_name=file_path.name)
                    if item_label:
                        log(f"Marked {item_label} complete in ROADMAP.md")
                except Exception as ex:
                    log(f"Failed to auto-mark roadmap: {ex}")
        else:
            log(f"Failed to complete {file_path.name} after {max_retries} attempts.")
            # Move to a failed queue
            failed_dest = completed_dir / (file_path.name + ".failed")
            shutil.move(file_path, failed_dest)
            
            # Circuit Breaker: Escalate to human by marking roadmap as [!]
            if file_path.name.startswith("gsd-phase-"):
                try:
                    phase_num_str = file_path.stem.replace("gsd-phase-", "")
                    roadmap_path = Path(".planning/ROADMAP.md").resolve()
                    if roadmap_path.exists():
                        content = roadmap_path.read_text(encoding="utf-8")
                        content = content.replace(f"- [ ] **Phase {phase_num_str}:", f"- [!] **Phase {phase_num_str}:")
                        roadmap_path.write_text(content, encoding="utf-8")
                        log(f"🚨 ESCALATION: Marked Phase {phase_num_str} as BLOCKED [!] in ROADMAP.md")
                except Exception as ex:
                    log(f"Failed to trigger circuit breaker: {ex}")

async def run_daemon(*, poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS, run_once: bool = False):
    state_dir = Path("state").resolve()
    inbox_dir = state_dir / "inbox"
    completed_dir = state_dir / "completed"
    improver_dir = Path("../Promptimprover").resolve()

    inbox_dir.mkdir(parents=True, exist_ok=True)
    completed_dir.mkdir(parents=True, exist_ok=True)

    log(f"Autonomous Daemon Online.")
    log(f"Inbox: {inbox_dir}")
    log(f"Completed: {completed_dir}")
    log("Drop a .md file with steering instructions into the inbox to begin.")

    while True:
        try:
            await process_inbox(inbox_dir, completed_dir, improver_dir)
        except Exception as exc:
            log(f"Daemon loop error: {exc!r}")
            if run_once:
                raise
            log(f"Cooling down for {DEFAULT_RETRY_DELAY_SECONDS:.0f}s before retry.")
            await asyncio.sleep(DEFAULT_RETRY_DELAY_SECONDS)
            continue
        if run_once:
            return
        await asyncio.sleep(poll_interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the autonomous MAF daemon.")
    parser.add_argument("--once", action="store_true", help="Process one poll cycle and exit.")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Seconds between inbox polls when running continuously.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    asyncio.run(run_daemon(poll_interval=args.poll_interval, run_once=args.once))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
