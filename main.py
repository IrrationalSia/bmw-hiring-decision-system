"""
BMW Hiring Decision System — end-to-end pipeline orchestrator.

Usage
-----
  # With .env file
  export $(cat .env | xargs) && python main.py          # Linux / Mac
  set ANTHROPIC_API_KEY=<key> && python main.py          # Windows CMD

  # Or with key already in environment
  python main.py

Output
------
  - Live console output via Rich
  - results.json  written to the project root
"""

import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.table import Table
from rich import box

from agents import jd_agent, cv_agent, scenario_agent, decision_agent
from data.synthetic_candidates import JOB_DESCRIPTION, CANDIDATES

load_dotenv()
console = Console()


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_with_spinner(description: str, fn, *args, **kwargs):
    """Run fn(*args) while showing a spinner; return the result."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task(description, total=None)
        result = fn(*args, **kwargs)
    return result


def score_bar(score: float, width: int = 20) -> str:
    filled = int(round(score / 100 * width))
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {score:.1f}"


def recommendation_style(rec: str) -> str:
    mapping = {
        "strong_hire": "[bold green]STRONG HIRE[/bold green]",
        "hire":        "[green]HIRE[/green]",
        "hold":        "[yellow]HOLD[/yellow]",
        "pass":        "[red]PASS[/red]",
    }
    return mapping.get(rec.lower(), rec.upper())


def confidence_style(conf: str) -> str:
    mapping = {
        "high":   "[bold green]HIGH[/bold green]",
        "medium": "[yellow]MEDIUM[/yellow]",
        "low":    "[bold red]LOW[/bold red]",
    }
    return mapping.get(conf.lower(), conf.upper())


def urgency_style(level: str) -> str:
    mapping = {
        "low":    "[green]LOW[/green]",
        "medium": "[yellow]MEDIUM[/yellow]",
        "high":   "[bold red]HIGH[/bold red]",
    }
    return mapping.get(level.lower(), level.upper())


# ── Pure pipeline (no console I/O) ───────────────────────────────────────────

def run_pipeline(job_description: str, candidates: list) -> dict:
    """
    Run the full 4-agent pipeline and return structured results.
    No console output — safe to call from API or tests.
    """
    results = {"jd_analysis": None, "candidates": []}

    jd_analysis = jd_agent.analyze_jd(job_description)
    results["jd_analysis"] = jd_analysis

    for candidate in candidates:
        cv_result       = cv_agent.score_candidate(candidate, jd_analysis)
        scenario_result = scenario_agent.apply_scenarios(cv_result, jd_analysis)
        decision        = decision_agent.make_decision(cv_result, scenario_result, jd_analysis)

        results["candidates"].append({
            "candidate":       candidate,
            "cv_result":       cv_result,
            "scenario_result": scenario_result,
            "decision":        decision,
        })

    return results


# ── Main pipeline ─────────────────────────────────────────────────────────────

def main():
    console.print()
    console.print(Panel.fit(
        "[bold white]BMW Group — Hiring Decision System[/bold white]\n"
        "[dim]Speed vs Right Hire  •  Multi-Agent Pipeline  •  claude-sonnet-4-6[/dim]",
        border_style="blue",
    ))
    console.print()

    # Delegate to the pure pipeline; print progress around each agent call
    # by wrapping run_pipeline's inner steps with spinners.
    results = {"jd_analysis": None, "candidates": []}

    # ── Step 1: JD Agent ──────────────────────────────────────────────────────
    console.print(Rule("[bold blue]Step 1 / 4  —  JD Agent[/bold blue]"))
    console.print("[dim]Extracting requirements and urgency signals from job description…[/dim]\n")

    jd_analysis = run_with_spinner(
        "Analysing job description…",
        jd_agent.analyze_jd,
        JOB_DESCRIPTION,
    )
    results["jd_analysis"] = jd_analysis

    urgency_level = jd_analysis.get("urgency_level", "unknown")
    console.print(f"  Urgency level   : {urgency_style(urgency_level)}")
    console.print(f"  Must-have reqs  : [bold]{len(jd_analysis.get('must_have', []))}[/bold]")
    console.print(f"  Nice-to-have    : [bold]{len(jd_analysis.get('nice_to_have', []))}[/bold]")
    console.print(f"  Urgency signals : [yellow]{', '.join(jd_analysis.get('urgency_signals', ['none']))}[/yellow]")
    console.print()

    # ── Steps 2–4: Per-candidate loop ─────────────────────────────────────────
    all_decisions = []

    for i, candidate in enumerate(CANDIDATES, start=1):
        name = candidate["name"]

        console.print(Rule(f"[bold blue]Candidate {i} / {len(CANDIDATES)}  —  {name}[/bold blue]"))

        console.print("[dim]  Step 2 / 4 — CV Agent: scoring against JD requirements…[/dim]")
        cv_result = run_with_spinner(f"Scoring {name}…", cv_agent.score_candidate, candidate, jd_analysis)

        console.print(f"  Baseline fit score : [bold]{cv_result.get('weighted_fit_score', 0):.1f}[/bold] / 100")
        bias_flags = cv_result.get("urgency_bias_flags_summary", [])
        if bias_flags:
            console.print(f"  Urgency-bias flags : [yellow]{', '.join(bias_flags)}[/yellow]")
        else:
            console.print("  Urgency-bias flags : [green]none detected[/green]")
        console.print()

        console.print("[dim]  Step 3 / 4 — Scenario Agent: applying BMW strategic scenarios…[/dim]")
        scenario_result = run_with_spinner(f"Applying scenarios for {name}…", scenario_agent.apply_scenarios, cv_result, jd_analysis)

        s = scenario_result.get("scenarios", {})
        console.print(f"  Transformation push   : [bold]{s.get('transformation_push',{}).get('adjusted_score', '?'):.1f}[/bold]")
        console.print(f"  Automotive continuity : [bold]{s.get('automotive_continuity',{}).get('adjusted_score', '?'):.1f}[/bold]")
        console.print(f"  Competitive pressure  : [bold]{s.get('competitive_pressure',{}).get('adjusted_score', '?'):.1f}[/bold]")
        console.print(f"  Best-fit scenario     : [cyan]{scenario_result.get('best_fit_scenario', '?')}[/cyan]")
        console.print()

        console.print("[dim]  Step 4 / 4 — Decision Agent: synthesising final recommendation…[/dim]")
        decision = run_with_spinner(f"Generating decision for {name}…", decision_agent.make_decision, cv_result, scenario_result, jd_analysis)

        console.print(f"  Recommendation    : {recommendation_style(decision.get('recommendation', ''))}")
        console.print(f"  Fit score         : [bold]{decision.get('fit_score', 0):.1f}[/bold] / 100")
        console.print(f"  Speed-pressure    : [bold]{decision.get('speed_pressure_score', 0):.1f}[/bold] / 100")
        console.print(f"  Confidence        : {confidence_style(decision.get('confidence_level', ''))}")
        if decision.get("urgency_warning"):
            console.print(f"  [bold red]Urgency warning[/bold red]: {decision['urgency_warning']}")
        console.print()

        all_decisions.append(decision)
        results["candidates"].append({
            "candidate": candidate,
            "cv_result": cv_result,
            "scenario_result": scenario_result,
            "decision": decision,
        })

    # ── Summary table ─────────────────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold white]Final Comparison — All Candidates[/bold white]"))
    console.print()

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white on blue",
        border_style="blue",
        title="Head of Production — Regensburg",
        expand=False,
    )

    table.add_column("Candidate",          style="bold",   min_width=22)
    table.add_column("Availability",       style="cyan",   min_width=14)
    table.add_column("Fit Score",          justify="right", min_width=10)
    table.add_column("Speed Pressure",     justify="right", min_width=14)
    table.add_column("Best Scenario",      style="italic", min_width=22)
    table.add_column("Recommendation",     min_width=14)
    table.add_column("Confidence",         min_width=10)

    for entry in results["candidates"]:
        d = entry["decision"]
        sr = entry["scenario_result"]
        cand = entry["candidate"]

        rec   = d.get("recommendation", "?")
        conf  = d.get("confidence_level", "?")
        fit   = d.get("fit_score", 0)
        speed = d.get("speed_pressure_score", 0)

        # Colour-code speed pressure
        if speed >= 60:
            speed_str = f"[bold red]{speed:.1f}[/bold red]"
        elif speed >= 30:
            speed_str = f"[yellow]{speed:.1f}[/yellow]"
        else:
            speed_str = f"[green]{speed:.1f}[/green]"

        table.add_row(
            cand["name"],
            cand["availability"],
            f"{fit:.1f}",
            speed_str,
            sr.get("best_fit_scenario", "?").replace("_", " ").title(),
            recommendation_style(rec),
            confidence_style(conf),
        )

    console.print(table)
    console.print()

    # ── Human-in-the-loop reminder ─────────────────────────────────────────────
    console.print(Panel(
        "[bold yellow]HUMAN OVERRIDE REQUIRED[/bold yellow]\n\n"
        "This system provides structured evidence and trade-off analysis.\n"
        "[bold]The final hiring decision rests entirely with the hiring manager.[/bold]\n\n"
        "Consider reviewing:\n"
        "  • Does the Speed-Pressure score change your ranking?\n"
        "  • What is the actual cost of a 4–8 week vacancy vs a weaker hire?\n"
        "  • Which BMW strategic scenario is most live right now?\n"
        "  • Have urgency-bias flags been checked against objective evidence?\n\n"
        "[dim]results.json written to project root for full detail.[/dim]",
        border_style="yellow",
        title="[bold yellow]⚠  Final Call: Hiring Manager[/bold yellow]",
    ))
    console.print()

    # ── Persist results ────────────────────────────────────────────────────────
    output_path = Path(__file__).parent / "results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    console.print(f"[dim]Full results saved to: {output_path}[/dim]\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"\n[bold red]Error:[/bold red] {exc}")
        sys.exit(1)
