"""
slack_blocks.py
────────────────────────────────────────────────────────────────
Block Kit formatters for all 4 RFP Agent outputs.
These functions return Slack Block Kit payloads ready to post.
"""

import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import config

# ─── VERDICT COLORS ──────────────────────────────────────────────────────────
VERDICT_EMOJI  = {"GREEN": ":large_green_circle:", "YELLOW": ":large_yellow_circle:", "RED": ":red_circle:"}
VERDICT_HEADER = {"GREEN": "GO — Pursue this deal", "YELLOW": "CONDITIONAL — Needs review before proceeding", "RED": "NO-GO — Do not pursue"}

# ─────────────────────────────────────────────────────────────────────────────
#  1. INTAKE SUMMARY (Phase 1)
# ─────────────────────────────────────────────────────────────────────────────
def build_intake_blocks(parsed: dict) -> list:
    """Quick intake summary block — posted while Go/No-Go is processing."""
    company   = parsed.get("company_name", "Unknown")
    industry  = parsed.get("industry", "Unknown")
    size      = parsed.get("company_size", "Unknown")
    deadline  = parsed.get("submission_deadline", "Unknown")
    volume    = parsed.get("estimated_annual_volume", "Unknown")
    sections  = len(parsed.get("sections", []))
    flags     = len(parsed.get("legal_flags", []))
    missing   = len(parsed.get("missing_info", []))

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f":clipboard: RFP Received — {company}"}},
        {"type": "section",
         "fields": [
             {"type": "mrkdwn", "text": f"*Company:*\n{company}"},
             {"type": "mrkdwn", "text": f"*Industry:*\n{industry}"},
             {"type": "mrkdwn", "text": f"*Size:*\n{size.title()}"},
             {"type": "mrkdwn", "text": f"*Deadline:*\n{deadline}"},
             {"type": "mrkdwn", "text": f"*Est. Volume:*\n{volume}"},
             {"type": "mrkdwn", "text": f"*Sections found:*\n{sections}"},
         ]},
    ]

    # Warn if legal flags found
    if flags > 0:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn",
                     "text": f":warning: *{flags} legal flag(s) detected* — Legal review required before proceeding.\n"
                             f"Also flagged {missing} missing info item(s) that will need clarification."}
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": ":hourglass_flowing_sand: Running Go/No-Go analysis... (~30 sec)"}]
    })
    return blocks


# ─────────────────────────────────────────────────────────────────────────────
#  2. GO/NO-GO BRIEF (Phase 2)
# ─────────────────────────────────────────────────────────────────────────────
def build_go_no_go_blocks(brief_text: str, parsed: dict) -> list:
    """Full Go/No-Go brief with approve/escalate/reject buttons."""
    company = parsed.get("company_name", "Unknown")

    # Extract verdict from first line
    verdict = "YELLOW"
    for line in brief_text.split("\n"):
        if line.startswith("RECOMMENDATION:"):
            verdict = line.replace("RECOMMENDATION:", "").strip()
            break

    emoji  = VERDICT_EMOJI.get(verdict, ":large_yellow_circle:")
    header = VERDICT_HEADER.get(verdict, "Review required")

    blocks = [
        {"type": "header",
         "text": {"type": "plain_text", "text": f"{emoji} Go/No-Go: {company}"}},
        {"type": "section",
         "text": {"type": "mrkdwn",
                  "text": f"*Decision: {verdict} — {header}*"}},
        {"type": "divider"},
    ]

    # Parse brief into sections and render each
    current_section = None
    current_lines   = []

    def flush(section, lines):
        if section and lines:
            body = "\n".join(l for l in lines if l.strip())
            if body:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{section}*\n{body}"}
                })

    known_headers = [
        "DEAL SNAPSHOT", "COMPETITIVE POSITION", "MARGIN ASSESSMENT",
        "STRATEGIC FIT", "LEGAL FLAGS", "RECOMMENDATION RATIONALE",
        "IF YELLOW", "IF YELLOW — CONDITIONS TO PROCEED:"
    ]

    for line in brief_text.split("\n"):
        if line.startswith("RECOMMENDATION:"):
            continue
        matched = next((h for h in known_headers if line.upper().startswith(h)), None)
        if matched:
            flush(current_section, current_lines)
            current_section = line.rstrip(":")
            current_lines   = []
        else:
            current_lines.append(line)

    flush(current_section, current_lines)

    # Action buttons — tagged with company name for callback routing
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn",
                 "text": "_React to approve, or use the buttons below to route this deal:_"}
    })
    blocks.append({
        "type": "actions",
        "elements": [
            {"type": "button", "style": "primary",
             "text": {"type": "plain_text", "text": ":white_check_mark: Approve — Pursue"},
             "value": f"approve|{company}", "action_id": "rfp_approve"},
            {"type": "button",
             "text": {"type": "plain_text", "text": ":warning: Escalate to Ryan"},
             "value": f"escalate|{company}", "action_id": "rfp_escalate"},
            {"type": "button", "style": "danger",
             "text": {"type": "plain_text", "text": ":x: Pass — No-Go"},
             "value": f"decline|{company}", "action_id": "rfp_decline"},
        ]
    })
    return blocks


# ─────────────────────────────────────────────────────────────────────────────
#  3. CLARIFICATION QUESTIONS (Phase 3)
# ─────────────────────────────────────────────────────────────────────────────
def build_questions_blocks(questions_text: str, parsed: dict) -> list:
    """Question list block — posted to thread, with internal routing note."""
    company = parsed.get("company_name", "Unknown")

    # Split at INTERNAL ROUTING NOTE if present
    public_part   = questions_text
    internal_part = None
    if "INTERNAL ROUTING NOTE" in questions_text:
        parts = questions_text.split("INTERNAL ROUTING NOTE", 1)
        public_part   = parts[0].strip()
        internal_part = parts[1].strip()

    blocks = [
        {"type": "header",
         "text": {"type": "plain_text", "text": f":question: Clarification Questions — {company}"}},
        {"type": "section",
         "text": {"type": "mrkdwn",
                  "text": "_The following question list is ready to send to the prospect. "
                          "Review before sending — internal routing note is below._"}},
        {"type": "divider"},
    ]

    # Chunk question text into Slack blocks (max 3000 chars per block)
    chunk_size = 2800
    chunks = [public_part[i:i+chunk_size] for i in range(0, len(public_part), chunk_size)]
    for chunk in chunks:
        blocks.append({"type": "section",
                       "text": {"type": "mrkdwn", "text": chunk}})

    # Internal routing note in a context block (visually distinct)
    if internal_part:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn",
                     "text": f":lock: *Internal Routing Note (do not send to prospect)*\n{internal_part[:2800]}"}
        })

    return blocks


# ─────────────────────────────────────────────────────────────────────────────
#  4. PROJECT BOARD (Phase 4)
# ─────────────────────────────────────────────────────────────────────────────
def build_project_board_blocks(tasks: list, parsed: dict) -> list:
    """Project board block — categorized sections with owners."""
    company = parsed.get("company_name", "Unknown")

    autopilot   = [t for t in tasks if t.get("category") == "AUTOPILOT"]
    needs_input = [t for t in tasks if t.get("category") == "NEEDS_INPUT"]
    legal       = [t for t in tasks if t.get("category") == "LEGAL_FLAG"]

    blocks = [
        {"type": "header",
         "text": {"type": "plain_text", "text": f":clipboard: Project Board — {company}"}},
        {"type": "section",
         "fields": [
             {"type": "mrkdwn", "text": f":large_green_circle: *AUTOPILOT:* {len(autopilot)} sections\n_Pre-filled from boilerplate_"},
             {"type": "mrkdwn", "text": f":large_yellow_circle: *NEEDS INPUT:* {len(needs_input)} sections\n_Require human work_"},
             {"type": "mrkdwn", "text": f":red_circle: *LEGAL FLAG:* {len(legal)} sections\n_Route to Legal immediately_"},
         ]},
        {"type": "divider"},
    ]

    # LEGAL first (most urgent)
    if legal:
        legal_lines = [f":red_circle: *LEGAL FLAG* — Route to Legal immediately"]
        for t in legal:
            pri   = t.get("priority", "medium").upper()
            owner = t.get("owner", "TBD")
            notes = t.get("notes", "")[:120]
            legal_lines.append(f"> `[{pri}]` *{t['section_name']}* → {owner}\n> _{notes}_")
        blocks.append({"type": "section",
                       "text": {"type": "mrkdwn", "text": "\n".join(legal_lines)}})
        blocks.append({"type": "divider"})

    # NEEDS INPUT
    if needs_input:
        ni_lines = [":large_yellow_circle: *NEEDS INPUT* — Assign and action"]
        for t in needs_input:
            pri   = t.get("priority", "medium").upper()
            owner = t.get("owner", "TBD")
            notes = t.get("notes", "")[:120]
            ni_lines.append(f"> `[{pri}]` *{t['section_name']}* → {owner}\n> _{notes}_")
        blocks.append({"type": "section",
                       "text": {"type": "mrkdwn", "text": "\n".join(ni_lines)}})
        blocks.append({"type": "divider"})

    # AUTOPILOT (collapsed — just a summary)
    if autopilot:
        auto_names = ", ".join(t["section_name"] for t in autopilot)
        blocks.append({"type": "section",
                       "text": {"type": "mrkdwn",
                                "text": f":large_green_circle: *AUTOPILOT* — Pre-filled from boilerplate (no action needed)\n_{auto_names}_"}})

    blocks.append({"type": "context",
                   "elements": [{"type": "mrkdwn",
                                 "text": ":page_facing_up: Full draft response .docx is attached above. "
                                         "AUTOPILOT sections are pre-filled. NEEDS INPUT sections are flagged."}]})
    return blocks


# ─────────────────────────────────────────────────────────────────────────────
#  5. AUTOPILOT PREVIEW (Phase 4b)
#     Shows actual pre-filled boilerplate answers in Slack so reps can
#     review and approve without opening the Word doc.
# ─────────────────────────────────────────────────────────────────────────────

# Maps section name keywords → (config key, friendly label)
AUTOPILOT_MAP = [
    (["company info", "company overview", "about us", "vendor company", "vendor info"],
     "company_overview_long",       "Company Overview"),
    (["contact", "primary contact", "account manager"],
     None,                          "Primary Contact"),
    (["fulfillment", "logistics", "delivery", "timing", "turnaround"],
     "fulfillment_process",         "Fulfillment & Delivery"),
    (["shipping", "ship", "transport"],
     "shipping_and_logistics",      "Shipping & Logistics"),
    (["sla", "service level", "guarantee", "turnaround"],
     "sla_standard",                "SLA & Satisfaction Guarantee"),
    (["design", "creative", "artwork", "artist", "graphic"],
     "design_capabilities",         "Design Capabilities"),
    (["portal", "ordering", "ecommerce", "platform", "reporting", "store"],
     "portal_capabilities",         "Online Portal & Reporting"),
    (["sustain", "environmental", "esg", "scope 3", "green"],
     "sustainability",              "Sustainability"),
    (["security", "compliance", "soc", "hipaa", "audit", "data"],
     "security_and_compliance",     "Security & Compliance"),
    (["financial", "stability", "bankruptcy", "litigation", "revenue"],
     "financial_disclosures",       "Financial Stability"),
    (["payment", "terms", "net ", "invoic", "billing"],
     "payment_terms_standard",      "Payment Terms"),
    (["background", "employee conduct", "code of conduct"],
     "background_checks",           "Background Checks & Conduct"),
    (["reference", "client list", "customer list", "confidential"],
     "client_confidentiality",      "Client Confidentiality Policy"),
    (["catalog", "product", "brand partner", "assortment"],
     "product_catalog_reference",   "Product Catalog"),
]


def _match_autopilot(section_name: str):
    """Return (config_key, friendly_label) for an AUTOPILOT section, or None."""
    lower = section_name.lower()
    for keywords, cfg_key, label in AUTOPILOT_MAP:
        if any(kw in lower for kw in keywords):
            return cfg_key, label
    return None, None


def _get_contact_block() -> str:
    """Build the primary contact answer string from config."""
    lines = []
    name  = getattr(config, "PRIMARY_CONTACT_NAME",  "")
    title = getattr(config, "PRIMARY_CONTACT_TITLE", "")
    phone = getattr(config, "PRIMARY_CONTACT_PHONE", "")
    email = getattr(config, "PRIMARY_CONTACT_EMAIL", "")
    if name:  lines.append(name)
    if title: lines.append(title)
    if phone or email:
        lines.append(" | ".join(filter(None, [phone, email])))
    return "\n".join(lines) if lines else "[Update PRIMARY_CONTACT fields in config.py]"


def build_autopilot_preview_blocks(tasks: list, parsed: dict) -> list:
    """
    Phase 4b — posts the actual boilerplate text for every AUTOPILOT section
    so reps can review in Slack without opening the Word doc.
    """
    company    = parsed.get("company_name", "Unknown")
    autopilot  = [t for t in tasks if t.get("category") == "AUTOPILOT"]

    if not autopilot:
        return []

    blocks = [
        {"type": "header",
         "text": {"type": "plain_text",
                  "text": f":large_green_circle: Auto-filled sections — {company}"}},
        {"type": "section",
         "text": {"type": "mrkdwn",
                  "text": (
                      f"*{len(autopilot)} sections pre-filled from approved boilerplate.* "
                      "Review below — these will appear verbatim in the draft .docx. "
                      "Reply in thread if any need updating before submission."
                  )}},
        {"type": "divider"},
    ]

    for task in autopilot:
        name     = task.get("section_name", "")
        cfg_key, label = _match_autopilot(name)

        # Get the actual content
        if cfg_key == "contact" or (cfg_key is None and "contact" in name.lower()):
            content = _get_contact_block()
        elif cfg_key and hasattr(config, "AUTOPILOT_CONTENT"):
            content = config.AUTOPILOT_CONTENT.get(cfg_key, "")
        else:
            content = ""

        if not content:
            content = (
                f"[Standard response — pull from approved boilerplate. "
                f"Update config.AUTOPILOT_CONTENT to add pre-filled text for '{name}'.]"
            )

        # Truncate for Slack (max 3000 chars per block, keep readable)
        preview = content[:600] + ("..." if len(content) > 600 else "")

        # Owner note
        owner    = task.get("owner", "Ryan Parrish")
        priority = task.get("priority", "low").upper()
        note     = task.get("notes", "")[:120]

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f":white_check_mark: *{name}*\n"
                    f"_{preview}_\n"
                    f"`Owner: {owner}` `{priority} priority`"
                    + (f"\n_{note}_" if note else "")
                )
            }
        })
        blocks.append({"type": "divider"})

    # Footer CTA
    blocks.append({
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": (
                ":pencil: *To update any boilerplate:* open `config.py` → edit the relevant "
                "`AUTOPILOT_CONTENT` entry → restart the bot. "
                "Changes apply to all future RFPs automatically."
            )
        }]
    })

    return blocks
