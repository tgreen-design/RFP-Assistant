═══════════════════════════════════════════════════════════════
  CUSTOMINK RFP AGENT — PROTOTYPE v1.0
  Sprint 1: Intake → Go/No-Go → Questions → Project Board
═══════════════════════════════════════════════════════════════

WHAT THIS IS
─────────────
A working Python prototype of the RFP AI Agent. Drop in an RFP
document, and it runs four phases automatically:

  Phase 1 — INTAKE PARSER
    Reads the raw RFP and extracts structured data:
    company, industry, deal size, deadline, sections,
    legal flags, missing information.

  Phase 2 — GO/NO-GO AGENT
    Produces a one-page GREEN / YELLOW / RED decision brief
    for Ryan and Haley. Covers competitive position, margin
    assessment, strategic fit, and legal flags.

  Phase 3 — QUESTION GENERATOR
    Drafts the full clarification question list using your
    standard question library + RFP-specific questions.
    Includes an internal routing note (what needs Ryan /
    Cody / Legal before sending).

  Phase 4 — PROJECT BOARD
    Categorizes every RFP section into AUTOPILOT /
    NEEDS INPUT / LEGAL FLAG and assigns section owners.

Files saved automatically to the rfp_output/ folder.


FILES IN THIS FOLDER
─────────────────────
  config.py        ← Edit this first (API key + your settings)
  rfp_agent.py     ← Main script — run this
  sample_rfp.txt   ← Example RFP (Meridian Health Systems)
  README.txt       ← This file
  rfp_output/      ← Where outputs are saved


STEP 1 — GET AN API KEY
─────────────────────────
You need an Anthropic API key to run this.

  1. Go to https://console.anthropic.com
  2. Sign in (or create an account using your work email)
  3. Click "API Keys" in the left sidebar
  4. Click "Create Key" — give it a name like "RFP Agent"
  5. Copy the key (it starts with sk-ant-...)

The key is only shown once — paste it somewhere safe.


STEP 2 — EDIT config.py
─────────────────────────
Open config.py and:

  1. Replace YOUR_API_KEY_HERE with your actual key:
       ANTHROPIC_API_KEY = "sk-ant-..."

  2. Review and update the business settings:
       MARGIN_FLOOR_PCT      — confirm with Cody Perry
       MARGIN_YELLOW_PCT     — confirm with Cody Perry
       MIN_DEAL_SIZE_USD     — confirm with Haley + Ryan
       WINNING_INDUSTRIES    — update if needed
       SECTION_OWNERS        — update with real team names
       COMPETITORS           — confirm with Martin
       AUTOPILOT_CONTENT     — paste in your approved boilerplate

  3. Save the file.


STEP 3 — INSTALL DEPENDENCIES
───────────────────────────────
You need Python 3.8+ installed. Then run this once:

  Mac/Linux:
    pip3 install anthropic "httpx[socks]"

  Windows:
    pip install anthropic "httpx[socks]"

If you get a "pip not found" error, try:
    python3 -m pip install anthropic "httpx[socks]"


STEP 4 — RUN THE AGENT
────────────────────────
  Mac/Linux:
    python3 rfp_agent.py

  Windows:
    python rfp_agent.py

You'll be asked:
  Choice 1 — Paste RFP text directly (type END when done)
  Choice 2 — Point to a file (e.g., sample_rfp.txt)

The agent will print progress for each phase and save a
full report to the rfp_output/ folder.


TIPS
─────
  - Paste the full RFP text for best results. Truncated RFPs
    produce weaker Go/No-Go briefs.

  - The agent uses two models:
    · claude-haiku  (fast, cheap) for Intake and Categorization
    · claude-opus   (thorough)   for Go/No-Go and Questions

  - Each full run costs approximately $0.15–$0.40 depending
    on RFP length. You can monitor usage at console.anthropic.com.

  - Outputs are saved as plain text. Future versions will
    output directly to Word documents and Slack.


WHAT'S COMING IN SPRINT 2
───────────────────────────
  - Salesforce webhook trigger (auto-runs when opp hits stage)
  - Slack bot delivery (outputs posted to #rfp-responses)
  - Word document output (formatted, ready-to-send)
  - Competitor price scraping (Vistaprint, RushOrderTees, etc.)
  - Product recommendation engine


QUESTIONS?
───────────
Talk to your implementation partner or refer to:
  RFP_Agent_Technical_Build_Plan.docx
  RFP_Agent_Prompts_and_Instructions.docx

═══════════════════════════════════════════════════════════════
