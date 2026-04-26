#!/usr/bin/env python3
"""
============================================================
  RFP AGENT PROTOTYPE — CustomInk Revenue Team
  Version 1.0 — Sprint 1 (Phases 1, 2, 3)

  WHAT THIS DOES:
  Phase 1 — Intake Parser:    Reads an RFP and extracts structured info
  Phase 2 — Go/No-Go Agent:   Scores the deal and writes a decision brief
  Phase 3 — Question Agent:   Drafts the clarification question list

  HOW TO RUN:
  1. Set your ANTHROPIC_API_KEY in config.py or as an environment variable
  2. Run:  python rfp_agent.py
  3. Paste your RFP text when prompted (or point to a file)

  OUTPUT:
  - Prints each phase result to the terminal
  - Saves a full report to rfp_output/[company_name]_[date].txt
============================================================
"""

import os, sys, json, textwrap
from datetime import datetime
from pathlib import Path

# Import config (make sure config.py is in the same folder)
sys.path.insert(0, str(Path(__file__).parent))
import config

# ── Setup Anthropic client ────────────────────────────────────────────────────
try:
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
except ImportError:
    print("ERROR: anthropic package not installed.")
    print("Run:  pip install anthropic")
    sys.exit(1)

# ── Output directory ─────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "rfp_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
#  HELPER: Call Claude
# ─────────────────────────────────────────────────────────────────────────────
def call_claude(system_prompt: str, user_message: str, model: str = None) -> str:
    """Send a prompt to Claude and return the text response."""
    model = model or config.MODEL_THOROUGH
    print(f"  [Calling Claude {model.split('-')[1]}...]", end="", flush=True)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    print(" done.")
    return response.content[0].text


# ─────────────────────────────────────────────────────────────────────────────
#  PHASE 1: INTAKE PARSER
# ─────────────────────────────────────────────────────────────────────────────
INTAKE_SYSTEM = """You are a document parsing assistant for CustomInk's Revenue team.
Your job is to extract structured information from incoming RFP documents.
CustomInk is a premium custom apparel and promotional products company serving enterprise clients.

When given an RFP document, extract the following fields.
Return ONLY a valid JSON object — no explanation, no markdown fences, just the JSON.

Required fields:
  company_name: string
  industry: string (best guess if not stated)
  company_size: string (small / mid-market / enterprise — infer from context)
  submission_deadline: string (e.g. "2026-05-15", or "unknown")
  estimated_annual_volume: string (units, dollar value, or "unknown")
  product_type: one of ["specific_products", "broad_categories", "unknown"]
  product_details: string (what they asked for)
  geographic_scope: string (e.g. "US only", "North America", "Global")
  evaluation_criteria: array of strings
  sections: array of {"section_name": string, "section_content": string}
  special_requirements: array of strings (kitting, fulfillment, security, etc.)
  legal_flags: array of strings (unusual T&Cs, non-standard terms, security requirements)
  missing_info: array of strings (things you could not determine from the document)

If a field cannot be determined, use "unknown" for strings or [] for arrays.
Do not guess — flag unknowns in missing_info."""

def run_intake(rfp_text: str) -> dict:
    """Phase 1: Parse the RFP into structured data."""
    print("\n" + "="*60)
    print("  PHASE 1 — INTAKE PARSER")
    print("="*60)

    result = call_claude(
        system_prompt=INTAKE_SYSTEM,
        user_message=f"Parse the following RFP document:\n\n{rfp_text}",
        model=config.MODEL_FAST
    )

    # Clean up JSON if Claude added any markdown
    result = result.strip()
    if result.startswith("```"):
        lines = result.split("\n")
        result = "\n".join(lines[1:-1])

    try:
        parsed = json.loads(result)
        print(f"\n  Company:      {parsed.get('company_name', 'Unknown')}")
        print(f"  Industry:     {parsed.get('industry', 'Unknown')}")
        print(f"  Size:         {parsed.get('company_size', 'Unknown')}")
        print(f"  Deadline:     {parsed.get('submission_deadline', 'Unknown')}")
        print(f"  Volume:       {parsed.get('estimated_annual_volume', 'Unknown')}")
        print(f"  Product type: {parsed.get('product_type', 'Unknown')}")
        print(f"  Sections:     {len(parsed.get('sections', []))} identified")
        print(f"  Legal flags:  {len(parsed.get('legal_flags', []))} found")
        print(f"  Missing info: {len(parsed.get('missing_info', []))} gaps")
        return parsed
    except json.JSONDecodeError:
        print("  WARNING: Could not parse JSON response. Returning raw text.")
        return {"raw": result, "company_name": "Unknown", "sections": []}


# ─────────────────────────────────────────────────────────────────────────────
#  PHASE 2: GO/NO-GO AGENT
# ─────────────────────────────────────────────────────────────────────────────
def build_go_no_go_system() -> str:
    winning = "\n".join(f"  - {i}" for i in config.WINNING_INDUSTRIES)
    challenges = "\n".join(f"  - {c}" for c in config.CHALLENGE_CONDITIONS)
    competitors = ", ".join(config.COMPETITORS)
    decision_makers = " and ".join(config.GO_NO_GO_OWNERS)

    return f"""You are a strategic deal analyst for {config.COMPANY_NAME}'s Revenue team.
You help the team decide whether an RFP is worth pursuing before any effort is invested.

Company context:
- {config.COMPANY_DESCRIPTION}
- Minimum acceptable gross margin: {config.MARGIN_FLOOR_PCT}%
- Yellow zone (escalate): below {config.MARGIN_YELLOW_PCT}%
- Minimum deal size worth pursuing: ${config.MIN_DEAL_SIZE_USD:,}/year
- We win most often in: {winning}
- We struggle when: {challenges}
- Key competitors: {competitors}

This brief will go directly to {decision_makers} for a fast decision.
Keep it to one page. Use plain language. Be direct about risks.

Format your response exactly like this:

RECOMMENDATION: [GREEN / YELLOW / RED]

DEAL SNAPSHOT
- Company: [name]
- Industry: [industry]
- Estimated annual value: [value or "Unknown — needs clarification"]
- Submission deadline: [date or "Unknown"]
- Product scope: [one sentence summary]
- Geographic scope: [US only / international / unknown]

COMPETITIVE POSITION
[2-3 sentences: how does our pricing likely compare to {competitors} for this profile?
Are we price-competitive, at-market, or at a premium? What does this mean for win probability?]

MARGIN ASSESSMENT
[2-3 sentences: estimated margin at our typical pricing for this order profile.
Flag if the deal likely requires below-floor pricing to be competitive.]

STRATEGIC FIT
[2-3 sentences: does this match our ideal customer? Red flags? Similar past wins?]

LEGAL FLAGS
[List any non-standard terms or clauses that need Legal review. "None identified" if clean.]

RECOMMENDATION RATIONALE
[2-3 sentences explaining the GREEN/YELLOW/RED call]

IF YELLOW — CONDITIONS TO PROCEED:
[List the specific answers or concessions that would change this to GREEN.
Skip this section if GREEN or RED.]"""

def run_go_no_go(parsed_rfp: dict) -> str:
    """Phase 2: Score the deal and produce the Go/No-Go brief."""
    print("\n" + "="*60)
    print("  PHASE 2 — GO/NO-GO AGENT")
    print("="*60)

    rfp_summary = json.dumps(parsed_rfp, indent=2)
    competitors_str = ", ".join(config.COMPETITORS)

    user_message = f"""Produce a Go/No-Go Brief for this RFP.

RFP SUMMARY (extracted by intake parser):
{rfp_summary}

COMPETITOR CONTEXT:
We do not have live pricing data yet (that requires the scraper to be set up).
Make reasonable assumptions based on the industry, product type, and order volume.
Note what pricing data would be needed to make a more precise assessment.
Known competitors to consider: {competitors_str}

MARGIN CONTEXT:
Our floor is {config.MARGIN_FLOOR_PCT}%. Our yellow zone is below {config.MARGIN_YELLOW_PCT}%.
Estimate whether this deal is likely above, in, or below those thresholds
based on the product type and volume described.

Produce the Go/No-Go Brief now."""

    result = call_claude(
        system_prompt=build_go_no_go_system(),
        user_message=user_message,
        model=config.MODEL_THOROUGH
    )

    # Extract and display recommendation
    for line in result.split("\n"):
        if line.startswith("RECOMMENDATION:"):
            rec = line.replace("RECOMMENDATION:", "").strip()
            color = {"GREEN": "\033[92m", "YELLOW": "\033[93m", "RED": "\033[91m"}.get(rec, "")
            reset = "\033[0m"
            print(f"\n  Decision: {color}{rec}{reset}")
            break

    return result


# ─────────────────────────────────────────────────────────────────────────────
#  PHASE 3: QUESTION AGENT
# ─────────────────────────────────────────────────────────────────────────────
QUESTION_SYSTEM = """You are a senior RFP analyst for CustomInk, a custom apparel and
promotional products company. Your job is to draft the clarification question list
that CustomInk will send to a prospect before writing an RFP response.

You have a standard question library by category. For each relevant category,
include the standard questions AND add any RFP-specific questions you observe.

STANDARD QUESTION LIBRARY:

KITTING & FULFILLMENT (include if RFP mentions kitting, warehousing, or fulfillment):
  - What is the anticipated frequency of kit orders?
  - What is the expected range of items per kit?
  - Will employees self-select products, or receive pre-defined kits?
  - What is the required turnaround time from order to delivery?
  - Is a returns/exchange process required? If so, who manages it?

INVENTORY MANAGEMENT (include if stocking or on-demand programs mentioned):
  - What is the expected number of active SKUs in the program?
  - Will inventory be managed on a buy-ahead or on-demand basis?
  - Who approves inventory replenishment orders?
  - What are the acceptable stock-out thresholds, if any?

INTERNATIONAL SHIPPING (include if international scope mentioned):
  - Which specific countries require fulfillment?
  - Are customs, duties, and import taxes to be included in pricing?
  - What is the estimated volume breakdown by country?
  - Are there country-specific regulatory or compliance requirements?

SECURITY & COMPLIANCE (include for enterprise clients or regulated industries):
  - Is a completed security questionnaire or SOC 2 Type II report required?
  - Are third-party vendor audits required? If so, at what frequency?
  - What employee or customer data, if any, would be shared with CustomInk?

PRODUCT & DECORATION (include always):
  - Do you have existing brand guidelines (logos, colors, approved fonts)?
  - Who has final approval authority on product designs and samples?
  - What is your expected sample approval timeline?
  - Are there any restricted materials, sustainability certifications, or
    country-of-origin requirements for products?

PRICING & PAYMENT (include always):
  - What is your estimated total annual spend for this program?
  - What are your preferred payment terms (Net 30, Net 60, etc.)?
  - Is a volume commitment or minimum annual order required in the contract?
  - Will pricing be fixed for the contract term, or subject to annual adjustment?

Format your output as a professional question document with:
1. An intro paragraph explaining why we're asking
2. Questions organized by category (only include categories that are relevant)
3. Each question on its own line, numbered within its category
4. A note at the end about the response deadline

Mark each question: [STANDARD] or [SPECIFIC TO THIS RFP]
This document will be sent directly to the prospect — write it professionally."""

def run_questions(parsed_rfp: dict) -> str:
    """Phase 3: Draft the clarification question list."""
    print("\n" + "="*60)
    print("  PHASE 3 — QUESTION GENERATOR")
    print("="*60)

    rfp_summary = json.dumps(parsed_rfp, indent=2)

    user_message = f"""Draft the clarification question list for this RFP.

RFP SUMMARY:
{rfp_summary}

QUESTION SUBMISSION DEADLINE: [TO BE SET — typically 5-7 business days after receipt]
PROSPECT RESPONSE DEADLINE: [TO BE SET — typically 1 week before our submission deadline]

Produce:
1. The formatted question document (ready to send to prospect)
2. After the document, add a short INTERNAL ROUTING NOTE:
   - Which questions require input from Ryan before we can send?
   - Which questions need input from Cody's team (pricing)?
   - Which need Legal review before we send?"""

    result = call_claude(
        system_prompt=QUESTION_SYSTEM,
        user_message=user_message,
        model=config.MODEL_THOROUGH
    )

    # Count questions
    question_count = sum(1 for line in result.split("\n")
                        if line.strip() and line.strip()[0].isdigit() and "." in line[:3])
    print(f"\n  Questions drafted: ~{question_count}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
#  PHASE 4: PROJECT BOARD CATEGORIZER (simplified)
# ─────────────────────────────────────────────────────────────────────────────
CATEGORIZE_SYSTEM = """You are a project coordinator for CustomInk's RFP response process.
Categorize each RFP section into one of three buckets and assign an owner.

Categories:
  AUTOPILOT — answered from standard boilerplate (company info, SLA, sustainability,
    financial disclosures, customer references, standard shipping info)
  NEEDS_INPUT — requires research or custom content (product recommendations,
    custom pricing, specific capability questions, client-specific use cases)
  LEGAL_FLAG — contains non-standard terms, unusual T&Cs, IP provisions,
    indemnification clauses, or contract language requiring Legal review

Return a JSON array only — no explanation:
[{
  "section_name": string,
  "category": "AUTOPILOT" | "NEEDS_INPUT" | "LEGAL_FLAG",
  "owner": string,
  "priority": "high" | "medium" | "low",
  "notes": string
}]"""

def run_categorize(parsed_rfp: dict) -> list:
    """Phase 4 (lite): Categorize sections and assign owners."""
    print("\n" + "="*60)
    print("  PHASE 4 — PROJECT BOARD (Section Categorization)")
    print("="*60)

    sections = parsed_rfp.get("sections", [])
    legal_flags = parsed_rfp.get("legal_flags", [])

    if not sections:
        print("  No sections found to categorize.")
        return []

    owners_str = json.dumps(config.SECTION_OWNERS, indent=2)
    sections_str = json.dumps(sections, indent=2)

    user_message = f"""Categorize these RFP sections and assign owners.

SECTIONS FROM RFP:
{sections_str}

LEGAL FLAGS ALREADY IDENTIFIED:
{json.dumps(legal_flags)}

OWNER ASSIGNMENTS TO USE:
{owners_str}

Return the JSON array of categorized tasks."""

    result = call_claude(
        system_prompt=CATEGORIZE_SYSTEM,
        user_message=user_message,
        model=config.MODEL_FAST
    )

    result = result.strip()
    if result.startswith("```"):
        lines = result.split("\n")
        result = "\n".join(lines[1:-1])

    try:
        tasks = json.loads(result)
        autopilot = [t for t in tasks if t["category"] == "AUTOPILOT"]
        needs_input = [t for t in tasks if t["category"] == "NEEDS_INPUT"]
        legal = [t for t in tasks if t["category"] == "LEGAL_FLAG"]

        print(f"\n  AUTOPILOT:   {len(autopilot)} sections (pre-filled automatically)")
        print(f"  NEEDS INPUT: {len(needs_input)} sections (require human work)")
        print(f"  LEGAL FLAGS: {len(legal)} sections (route to Legal immediately)")
        return tasks
    except json.JSONDecodeError:
        print("  WARNING: Could not parse task JSON.")
        return []


# ─────────────────────────────────────────────────────────────────────────────
#  SAVE OUTPUT
# ─────────────────────────────────────────────────────────────────────────────
def save_output(company: str, intake: dict, go_no_go: str, questions: str, tasks: list):
    """Save all phase outputs to a text file."""
    safe_name = company.replace(" ", "_").replace("/", "-")[:30]
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    filename = OUTPUT_DIR / f"{safe_name}_{date_str}.txt"

    divider = "\n" + "="*60 + "\n"

    content = f"""CUSTOMINK RFP AGENT — OUTPUT REPORT
Generated: {datetime.now().strftime("%B %d, %Y %I:%M %p")}
Company: {company}
{divider}
PHASE 1 — INTAKE SUMMARY
{divider}
{json.dumps(intake, indent=2)}
{divider}
PHASE 2 — GO/NO-GO BRIEF
{divider}
{go_no_go}
{divider}
PHASE 3 — CLARIFICATION QUESTIONS
{divider}
{questions}
{divider}
PHASE 4 — PROJECT BOARD TASKS
{divider}
"""
    for task in tasks:
        content += f"[{task['category']}] {task['section_name']}\n"
        content += f"  Owner: {task['owner']} | Priority: {task['priority']}\n"
        content += f"  Notes: {task['notes']}\n\n"

    filename.write_text(content)
    return filename


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("  CUSTOMINK RFP AGENT — PROTOTYPE v1.0")
    print("  Phases: Intake → Go/No-Go → Questions → Project Board")
    print("="*60)

    # Check API key
    if config.ANTHROPIC_API_KEY == "YOUR_API_KEY_HERE":
        print("\nERROR: Please set your Anthropic API key in config.py")
        print("  Get one at: https://console.anthropic.com")
        sys.exit(1)

    # Get RFP input
    print("\nHow would you like to provide the RFP?")
    print("  1. Paste text directly")
    print("  2. Load from a file")
    choice = input("\nChoice (1 or 2): ").strip()

    if choice == "2":
        filepath = input("File path: ").strip()
        rfp_text = Path(filepath).read_text()
        print(f"  Loaded {len(rfp_text):,} characters from {filepath}")
    else:
        print("\nPaste the RFP text below.")
        print("When done, type END on a new line and press Enter:")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        rfp_text = "\n".join(lines)
        print(f"  Received {len(rfp_text):,} characters")

    if len(rfp_text) < 50:
        print("ERROR: RFP text too short. Please provide the full document.")
        sys.exit(1)

    # Run all phases
    intake   = run_intake(rfp_text)
    go_no_go = run_go_no_go(intake)
    questions = run_questions(intake)
    tasks    = run_categorize(intake)

    # Print full Go/No-Go brief
    print("\n" + "="*60)
    print("  GO/NO-GO BRIEF (full)")
    print("="*60)
    print(go_no_go)

    # Print question list
    print("\n" + "="*60)
    print("  CLARIFICATION QUESTIONS (full)")
    print("="*60)
    print(questions)

    # Save
    company = intake.get("company_name", "Unknown")
    output_file = save_output(company, intake, go_no_go, questions, tasks)
    print(f"\n{'='*60}")
    print(f"  DONE — Full report saved to:")
    print(f"  {output_file}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
