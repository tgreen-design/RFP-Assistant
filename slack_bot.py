"""
============================================================
  CUSTOMINK RFP AGENT — Slack Bot
  Version 1.0

  HOW REPS USE IT:
  ─────────────────
  In any Slack channel or DM with the bot:

    /rfp                   → opens a modal to paste or describe the RFP
    /rfp-file              → uploads an RFP file (txt, docx, pdf)

  The bot then:
    1. Parses the RFP and posts an intake summary (Phase 1)
    2. Runs Go/No-Go analysis and posts a GREEN/YELLOW/RED brief
       with Approve / Escalate / Pass buttons (Phase 2)
    3. Posts the clarification question list (Phase 3)
    4. Posts the project board with section owners (Phase 4)
    4b. Posts all AUTOPILOT answers inline so reps can review
       boilerplate without opening the Word doc (Phase 4b)
    5. Generates and uploads the full draft .docx response

  HOW TO RUN:
  ────────────
  1. Copy .env.example → .env and fill in your Slack tokens + Anthropic key
  2. pip install -r requirements.txt
  3. python slack_bot.py

  SETUP GUIDE: See SLACK_SETUP.txt for creating the Slack App
============================================================
"""

import os, sys, json, threading
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ── Validate environment ──────────────────────────────────────────────────────
REQUIRED_ENV = ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET", "ANTHROPIC_API_KEY"]
missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
if missing:
    print(f"ERROR: Missing environment variables: {', '.join(missing)}")
    print("Copy .env.example to .env and fill in the values.")
    sys.exit(1)

# ── Imports ───────────────────────────────────────────────────────────────────
try:
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
except ImportError:
    print("ERROR: slack-bolt not installed. Run: pip install slack-bolt")
    sys.exit(1)

# Local modules
sys.path.insert(0, str(Path(__file__).parent))
import config
from rfp_agent import run_intake, run_go_no_go, run_questions, run_categorize
from slack_blocks import (
    build_intake_blocks, build_go_no_go_blocks,
    build_questions_blocks, build_project_board_blocks,
    build_autopilot_preview_blocks
)
from draft_generator import generate_draft

# ── Slack App ─────────────────────────────────────────────────────────────────
app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

# ─────────────────────────────────────────────────────────────────────────────
#  /rfp SLASH COMMAND — Opens the RFP input modal
# ─────────────────────────────────────────────────────────────────────────────
@app.command("/rfp")
def handle_rfp_command(ack, body, client):
    """Opens the RFP paste modal when rep types /rfp."""
    ack()

    trigger_id  = body["trigger_id"]
    channel_id  = body.get("channel_id", "")
    user_id     = body.get("user_id", "")

    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "rfp_submit_modal",
            "private_metadata": json.dumps({"channel_id": channel_id, "user_id": user_id}),
            "title": {"type": "plain_text", "text": "Submit an RFP"},
            "submit": {"type": "plain_text", "text": "Run RFP Agent"},
            "close":  {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            "*The RFP Agent will run 4 phases automatically:*\n"
                            "1. Parse the RFP and extract key facts\n"
                            "2. Run Go/No-Go analysis (GREEN / YELLOW / RED)\n"
                            "3. Draft the clarification question list\n"
                            "4. Build the project board with section owners\n"
                            "5. Generate and upload the full draft response .docx\n\n"
                            "_Typically takes 60–90 seconds._"
                        )
                    }
                },
                {"type": "divider"},
                {
                    "type": "input",
                    "block_id": "rfp_text_block",
                    "label": {"type": "plain_text", "text": "Paste the full RFP text"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "rfp_text_input",
                        "multiline": True,
                        "min_length": 100,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Paste the complete RFP document text here. Include all sections — the more complete the text, the better the analysis."
                        }
                    }
                },
                {
                    "type": "input",
                    "block_id": "rfp_channel_block",
                    "label": {"type": "plain_text", "text": "Post results to channel"},
                    "element": {
                        "type": "channels_select",
                        "action_id": "rfp_channel_select",
                        "placeholder": {"type": "plain_text", "text": "Select channel"}
                    },
                    "optional": True,
                    "hint": {
                        "type": "plain_text",
                        "text": "Leave blank to post results here in the current channel."
                    }
                },
                {
                    "type": "input",
                    "block_id": "rfp_note_block",
                    "label": {"type": "plain_text", "text": "Any context to add?"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "rfp_note_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "e.g. 'We have a relationship with this company' or 'Came in via Martin — treat as priority'"
                        }
                    },
                    "optional": True
                }
            ]
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
#  MODAL SUBMISSION — Runs all 4 phases
# ─────────────────────────────────────────────────────────────────────────────
@app.view("rfp_submit_modal")
def handle_rfp_submission(ack, body, client, view):
    """Fires when the rep submits the RFP modal. Kicks off processing."""
    ack()

    values   = view["state"]["values"]
    metadata = json.loads(view.get("private_metadata", "{}"))

    rfp_text    = values["rfp_text_block"]["rfp_text_input"]["value"]
    rep_note    = values.get("rfp_note_block", {}).get("rfp_note_input", {}).get("value") or ""
    channel_sel = values.get("rfp_channel_block", {}).get("rfp_channel_select", {}).get("selected_channel")

    # Determine output channel
    target_channel = channel_sel or metadata.get("channel_id") or os.getenv("RFP_DEFAULT_CHANNEL", "")
    user_id        = metadata.get("user_id", "")

    # Post "working" message immediately
    processing_msg = client.chat_postMessage(
        channel=target_channel,
        text=f":hourglass_flowing_sand: <@{user_id}> submitted an RFP — processing now...",
        blocks=[
            {"type": "section",
             "text": {"type": "mrkdwn",
                      "text": f":hourglass_flowing_sand: <@{user_id}> submitted an RFP — running intake analysis..."}},
            {"type": "context",
             "elements": [{"type": "mrkdwn",
                           "text": "Phase 1 of 4 running. This takes about 60–90 seconds."}]}
        ]
    )
    parent_ts = processing_msg["ts"]

    # Run all phases in a background thread so Slack doesn't time out
    def run_agent():
        try:
            _run_all_phases(
                client=client,
                channel=target_channel,
                parent_ts=parent_ts,
                rfp_text=rfp_text,
                rep_note=rep_note,
                user_id=user_id,
            )
        except Exception as e:
            client.chat_postMessage(
                channel=target_channel,
                thread_ts=parent_ts,
                text=f":x: RFP Agent error: `{str(e)[:500]}`\n\nPlease check the bot logs or try again."
            )

    threading.Thread(target=run_agent, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
#  CORE: Run all 4 phases and post results
# ─────────────────────────────────────────────────────────────────────────────
def _run_all_phases(client, channel, parent_ts, rfp_text, rep_note, user_id):
    """
    Runs all 4 phases sequentially, updating Slack as each phase completes.
    All output is posted to the thread of the parent message.
    """

    # ── PHASE 1: Intake ───────────────────────────────────────────────────
    _update_progress(client, channel, parent_ts, "Phase 1 of 4: Parsing RFP...", 1)
    parsed = run_intake(rfp_text)

    # Post intake summary
    client.chat_postMessage(
        channel=channel,
        thread_ts=parent_ts,
        blocks=build_intake_blocks(parsed),
        text=f"RFP parsed: {parsed.get('company_name', 'Unknown Company')}"
    )

    # ── PHASE 2: Go/No-Go ─────────────────────────────────────────────────
    _update_progress(client, channel, parent_ts, "Phase 2 of 4: Running Go/No-Go analysis...", 2)
    go_no_go = run_go_no_go(parsed)

    client.chat_postMessage(
        channel=channel,
        thread_ts=parent_ts,
        blocks=build_go_no_go_blocks(go_no_go, parsed),
        text=f"Go/No-Go brief for {parsed.get('company_name', 'Unknown')}"
    )

    # ── PHASE 3: Questions ────────────────────────────────────────────────
    _update_progress(client, channel, parent_ts, "Phase 3 of 4: Drafting clarification questions...", 3)
    questions = run_questions(parsed)

    client.chat_postMessage(
        channel=channel,
        thread_ts=parent_ts,
        blocks=build_questions_blocks(questions, parsed),
        text=f"Clarification questions for {parsed.get('company_name', 'Unknown')}"
    )

    # ── PHASE 4: Project Board ────────────────────────────────────────────
    _update_progress(client, channel, parent_ts, "Phase 4 of 4: Building project board...", 4)
    tasks = run_categorize(parsed)

    client.chat_postMessage(
        channel=channel,
        thread_ts=parent_ts,
        blocks=build_project_board_blocks(tasks, parsed),
        text=f"Project board for {parsed.get('company_name', 'Unknown')}"
    )

    # ── PHASE 4b: Autopilot Preview ───────────────────────────────────────
    # Show the actual boilerplate answers in Slack so reps don't have to
    # open the Word doc just to see what got pre-filled.
    autopilot_blocks = build_autopilot_preview_blocks(tasks, parsed)
    if autopilot_blocks:
        client.chat_postMessage(
            channel=channel,
            thread_ts=parent_ts,
            blocks=autopilot_blocks,
            text=f"Auto-filled sections for {parsed.get('company_name', 'Unknown')}"
        )

    # ── DRAFT DOC ──────────────────────────────────────────────────────────
    _update_progress(client, channel, parent_ts, "Generating draft response .docx...", 4)
    draft_path = generate_draft(parsed, tasks, go_no_go, questions)

    if draft_path and draft_path.exists():
        company = parsed.get("company_name", "Company")
        with open(draft_path, "rb") as f:
            client.files_upload_v2(
                channel=channel,
                thread_ts=parent_ts,
                file=f,
                filename=draft_path.name,
                title=f"{company} — Draft RFP Response",
                initial_comment=(
                    f":page_facing_up: *Draft response ready for {company}.*\n"
                    ":large_green_circle: Green sections = auto-filled from boilerplate\n"
                    ":large_yellow_circle: Yellow sections = need your team's input\n"
                    ":red_circle: Red sections = Legal review required before completing"
                )
            )

    # ── FINAL SUMMARY ─────────────────────────────────────────────────────
    autopilot   = len([t for t in tasks if t.get("category") == "AUTOPILOT"])
    needs_input = len([t for t in tasks if t.get("category") == "NEEDS_INPUT"])
    legal       = len([t for t in tasks if t.get("category") == "LEGAL_FLAG"])

    # Extract verdict
    verdict = "YELLOW"
    for line in go_no_go.split("\n"):
        if line.startswith("RECOMMENDATION:"):
            verdict = line.replace("RECOMMENDATION:", "").strip()
            break

    emoji_map = {"GREEN": ":large_green_circle:", "YELLOW": ":large_yellow_circle:", "RED": ":red_circle:"}

    client.chat_update(
        channel=channel,
        ts=parent_ts,
        text=f"RFP Agent complete: {parsed.get('company_name', 'Unknown')}",
        blocks=[
            {"type": "header",
             "text": {"type": "plain_text",
                      "text": f":robot_face: RFP Agent Complete — {parsed.get('company_name', 'Unknown')}"}},
            {"type": "section",
             "fields": [
                 {"type": "mrkdwn", "text": f"*Verdict:*\n{emoji_map.get(verdict, '')} {verdict}"},
                 {"type": "mrkdwn", "text": f"*Submitted by:*\n<@{user_id}>"},
                 {"type": "mrkdwn", "text": f"*AUTOPILOT sections:*\n{autopilot} pre-filled"},
                 {"type": "mrkdwn", "text": f"*Needs input:*\n{needs_input} sections"},
                 {"type": "mrkdwn", "text": f"*Legal flags:*\n{legal} items to review"},
             ]},
            {"type": "context",
             "elements": [{"type": "mrkdwn",
                           "text": ":thread: Full details in the thread below. Draft .docx attached."}]}
        ]
    )


def _update_progress(client, channel, ts, message, phase_num):
    """Update the parent message to show current phase progress."""
    try:
        client.chat_update(
            channel=channel,
            ts=ts,
            text=message,
            blocks=[
                {"type": "section",
                 "text": {"type": "mrkdwn", "text": f":hourglass_flowing_sand: *{message}*"}},
                {"type": "context",
                 "elements": [{"type": "mrkdwn",
                               "text": f"Phase {phase_num} of 4 | Use `/rfp` to submit another RFP"}]}
            ]
        )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  BUTTON HANDLERS — Approve / Escalate / Pass
# ─────────────────────────────────────────────────────────────────────────────
@app.action("rfp_approve")
def handle_approve(ack, body, client):
    ack()
    value    = body["actions"][0]["value"]
    company  = value.split("|", 1)[1] if "|" in value else value
    user_id  = body["user"]["id"]
    channel  = body["container"]["channel_id"]
    msg_ts   = body["container"]["message_ts"]

    client.chat_postMessage(
        channel=channel,
        thread_ts=msg_ts,
        text=f":white_check_mark: <@{user_id}> approved pursuing *{company}*. "
             f"Moving to Kickoff & Project Setup. Tagging <@{config.PRIMARY_CONTACT_SLACK_ID}> to assign."
    )


@app.action("rfp_escalate")
def handle_escalate(ack, body, client):
    ack()
    value   = body["actions"][0]["value"]
    company = value.split("|", 1)[1] if "|" in value else value
    user_id = body["user"]["id"]
    channel = body["container"]["channel_id"]
    msg_ts  = body["container"]["message_ts"]

    client.chat_postMessage(
        channel=channel,
        thread_ts=msg_ts,
        text=f":warning: <@{user_id}> escalated *{company}* for review. "
             f"Pinging <@{config.GO_NO_GO_SLACK_IDS[0]}> — please review the brief above and make the call."
    )


@app.action("rfp_decline")
def handle_decline(ack, body, client):
    ack()
    value   = body["actions"][0]["value"]
    company = value.split("|", 1)[1] if "|" in value else value
    user_id = body["user"]["id"]
    channel = body["container"]["channel_id"]
    msg_ts  = body["container"]["message_ts"]

    client.chat_postMessage(
        channel=channel,
        thread_ts=msg_ts,
        text=f":x: <@{user_id}> marked *{company}* as No-Go. "
             f"No further action needed. This thread will be archived in Salesforce."
    )


# ─────────────────────────────────────────────────────────────────────────────
#  START
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app_token = os.getenv("SLACK_APP_TOKEN")
    if not app_token:
        print("ERROR: SLACK_APP_TOKEN not set. Add it to your .env file.")
        print("Get it from: api.slack.com → Your App → Socket Mode → App-Level Tokens")
        sys.exit(1)

    print("=" * 60)
    print("  CUSTOMINK RFP AGENT — Slack Bot")
    print("  Listening for /rfp commands...")
    print("=" * 60)

    handler = SocketModeHandler(app, app_token)
    handler.start()
