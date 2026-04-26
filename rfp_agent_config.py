# ============================================================
#  RFP AGENT PROTOTYPE — Configuration
#  CustomInk Revenue Team
#
#  HOW TO USE:
#  1. Add your Anthropic API key below (get one at console.anthropic.com)
#  2. Fill in the CustomInk-specific values (work through these with Cody + Haley)
#  3. Add competitor site names and your margin floors
# ============================================================

import os

# ── API KEY ──────────────────────────────────────────────────
# Option A: Set it here directly (simpler, don't share this file)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_API_KEY_HERE")

# ── AI MODELS ────────────────────────────────────────────────
# Fast + cheap — used for extraction and categorization
MODEL_FAST = "claude-haiku-4-5-20251001"
# Thorough — used for reasoning, recommendations, drafting
MODEL_THOROUGH = "claude-opus-4-6"

# ── CUSTOMINK BUSINESS CONTEXT ───────────────────────────────
# Fill these in with Cody Perry and Haley before going live

COMPANY_NAME = "CustomInk"
COMPANY_DESCRIPTION = (
    "CustomInk is a custom apparel and promotional products company with 25+ years "
    "in business, 600+ employees, and 100,000+ customers served annually. "
    "We serve enterprise clients with branded apparel, promotional products, and "
    "end-to-end merchandise programs including online stores, kitting, and fulfillment. "
    "Headquartered in McLean, VA. CEO: David Doctorow. CRO: Ryan Massimo."
)

# Margin thresholds — confirm with Cody Perry (Loyalty Team)
MARGIN_FLOOR_PCT = 20          # Below this → RED (do not proceed without exec approval)
MARGIN_YELLOW_PCT = 28         # Below this → YELLOW (escalate to manager)
MARGIN_GREEN_PCT = 28          # Above this → GREEN (rep can approve)

# Deal size thresholds — confirm with Haley + Ryan
MIN_DEAL_SIZE_USD = 25000      # Below this → likely not worth pursuing

# Best-fit industries for CustomInk (where you win most)
WINNING_INDUSTRIES = [
    "Technology", "Financial Services", "Healthcare", "Retail",
    "Professional Services", "Non-Profit", "Sports & Entertainment"
]

# Conditions where you typically struggle
CHALLENGE_CONDITIONS = [
    "Price is the sole evaluation criterion",
    "International fulfillment required at significant scale",
    "Very short lead times (under 2 weeks) for large volumes",
    "Order volumes below minimum thresholds",
    "Highly commoditized product categories only"
]

# ── TEAM OWNERSHIP ───────────────────────────────────────────
# Maps section types to the person responsible — update with your team
SECTION_OWNERS = {
    "AUTOPILOT":      "Ryan Parrish",   # Spot-check only
    "PRODUCT":        "Jess Thatcher",  # Product SME
    "PRICING":        "Cody Perry",     # Loyalty Team
    "LEGAL":          "Legal Team",     # Legal review
    "CAPABILITIES":   "Ryan Parrish",
    "NEEDS_INPUT":    "Ryan Parrish",
}

# ── COMPETITORS TO MONITOR ───────────────────────────────────
# Confirm final list with Martin
COMPETITORS = [
    "Vistaprint",
    "Printful",
    "RushOrderTees",
    "Canva Print",
    "Zazzle",
]

# ── PRIMARY CONTACT (the rep / AE submitting RFPs) ───────────
# Update per-rep if needed, or set dynamically in Salesforce
PRIMARY_CONTACT_NAME          = "Kate Morton"
PRIMARY_CONTACT_TITLE         = "Account Executive"
PRIMARY_CONTACT_PHONE         = "(530) 302-2886"
PRIMARY_CONTACT_EMAIL         = "kate.morton@customink.com"
PRIMARY_CONTACT_SLACK_ID      = "UXXXXXXXX"   # ← replace with Kate's Slack member ID

# ── GO/NO-GO DECISION MAKERS ─────────────────────────────────
GO_NO_GO_OWNERS         = ["Haley", "Ryan Parrish"]
GO_NO_GO_SLACK_IDS      = ["UXXXXXXXX", "UXXXXXXXX"]  # ← replace with Haley's + Ryan's Slack member IDs

# ── SLACK CHANNEL (where agent posts RFP results) ─────────────
# Rep can override this at submission time, but this is the default
RFP_DEFAULT_CHANNEL = "#rfp-responses"   # ← create this channel in Slack first

# ── AUTOPILOT CONTENT ────────────────────────────────────────
# Paste your approved boilerplate here — these get inserted automatically
# into the relevant RFP sections. Update whenever content changes.
AUTOPILOT_CONTENT = {

    # ── COMPANY INFORMATION ──────────────────────────────────────────────────
    # Source: Crunch Fitness RFP response (Section 5.2, 5.4), verified 2026
    "company_overview_short": (
        "CustomInk, LLC (subsidiary of CustomInk Parent, LLC). "
        "1640 Boro Place, STE 301, McLean VA 22102. Website: customink.com. "
        "25+ years in business. Approximately 600 employees. 100,000+ customers served annually."
    ),
    "company_overview_long": (
        "CustomInk is one of the leading custom apparel and promotional products companies "
        "in the United States, with 25+ years in business and 600+ employees. We serve over "
        "100,000 customers per year ranging from small businesses to large enterprise accounts. "
        "Our leadership team: David Doctorow (CEO), Ryan Massimo (Chief Revenue Officer), "
        "Justin Sweitlik (Chief Technology Officer). We are privately held and headquartered "
        "in McLean, Virginia."
    ),

    # ── FINANCIAL / LEGAL DISCLOSURES ───────────────────────────────────────
    # Source: Crunch Fitness RFP response (Section 5.4.8–5.4.11), verified 2026
    "financial_disclosures": (
        "CustomInk has not filed for bankruptcy or sought creditor protection in the past 10 years. "
        "No liens have been placed against the company outside of traditional financing relationships. "
        "No significant litigation in the past 3 years. CustomInk is privately held and does not "
        "publicly disclose financial statements. We can provide a bank reference letter or "
        "Dun & Bradstreet report upon request. Certificate of insurance available upon request."
    ),

    # ── FULFILLMENT & DELIVERY ───────────────────────────────────────────────
    # Source: Crunch Fitness RFP response (Section 5.7, 5.8), verified 2026
    "fulfillment_process": (
        "CustomInk efficiently manages its order-to-fulfillment process using advanced in-house "
        "systems. Standard bulk orders are guaranteed to deliver within 14 business days (free "
        "shipping included). Rush and expedited options are available for most orders. "
        "Online Stores: 12-14 business days after order fulfillment. "
        "We have unlimited capacity — we support 100,000+ customers per year with production "
        "facilities across North America."
    ),
    "shipping_and_logistics": (
        "CustomInk ships to all 48 contiguous US states and DC as standard. International "
        "shipping is available. Domestic: via UPS with guaranteed delivery dates on bulk orders. "
        "International: 2 weeks domestic standard, 4 weeks international standard; rush ship "
        "options always available. We use freight brokers for international routing to ensure "
        "most economical and efficient paths. Countries of production: USA, Canada, and Mexico."
    ),
    "sla_standard": (
        "Standard bulk orders guaranteed to deliver within 14 business days (free shipping). "
        "Expedited options available for most orders. Online Stores: 12-14 days after "
        "order fulfillment. Design proof turnaround: typically within 1 business day. "
        "We deliver high-quality products that match what was created on our site. If for any "
        "reason you are not satisfied, we will work to make it right through reprinting or "
        "credit. Quantities do not affect standard turnaround times."
    ),

    # ── DESIGN CAPABILITIES ──────────────────────────────────────────────────
    # Source: Crunch Fitness RFP response (Section 5.5.3, 5.8.11), verified 2026
    "design_capabilities": (
        "CustomInk has multiple teams of expert artists who assist with designs. Depending on "
        "order type, design services are included at no additional charge. Our team reviews "
        "every design for quality — ensuring logos, colors, and approved fonts are accurate "
        "before production. Artists can generally turn around a proof within one business day. "
        "We can source unique promo items and new brands upon client request."
    ),

    # ── ONLINE PORTAL / E-COMMERCE ───────────────────────────────────────────
    # Source: Crunch Fitness RFP response (Section 5.6), verified 2026
    "portal_capabilities": (
        "CustomInk can set up a branded online ordering portal/store within 2 business days. "
        "No setup fee. No ongoing licensing fee (print minimums must be met for order "
        "fulfillment). The portal supports reporting and analytics including: buyer name, "
        "order number, timestamps, quantities, and product details. "
        "The organizer (client) has full dashboard access to manage the store. "
        "Reports can be pulled manually for preferred audiences. "
        "CustomInk can support parent/child account relationships for franchise/subsidiary models."
    ),

    # ── SUSTAINABILITY ───────────────────────────────────────────────────────
    # Source: Crunch Fitness RFP response (Section 5.4.18), KVYO RFI, verified 2026
    "sustainability": (
        "CustomInk's sustainability initiatives include packaging that uses less plastic and "
        "cardboard, a shift toward recycled materials, and ongoing supply chain sustainability "
        "programs. We work with eco-conscious suppliers and can provide a current sustainability "
        "report or disclosure upon request. We can report on program-level sustainability "
        "metrics for enterprise clients."
    ),

    # ── SECURITY & COMPLIANCE ────────────────────────────────────────────────
    # Source: KVYO RFI response (Platform Security), verified 2026
    "security_and_compliance": (
        "CustomInk maintains robust security and compliance standards. We can provide our "
        "SOC 2 Type II certification and PCI compliance documentation upon request. "
        "We perform background checks on every new US-based full-time or part-time employee "
        "at time of hire. CustomInk has an employee code of conduct addressing anti-harassment, "
        "ethics, and conduct standards."
    ),

    # ── PAYMENT TERMS ────────────────────────────────────────────────────────
    # Source: Crunch Fitness RFP response (Section 5.3, 5.10), verified 2026
    "payment_terms_standard": (
        "CustomInk accepts ACH, credit card, and other standard payment methods. "
        "We can accommodate extended payment terms (Net 30, 60, 90) for qualified enterprise "
        "accounts with creditworthiness verification and Finance approval. "
        "Net 90 is accepted with the understanding that creditworthiness must first be "
        "established per CustomInk's standard credit review process."
    ),

    # ── CLIENT CONFIDENTIALITY ───────────────────────────────────────────────
    # Source: Crunch Fitness RFP response (Section 5.1.4, 5.4.12), verified 2026
    "client_confidentiality": (
        "We are not at liberty to disclose our customer base without prior client approval. "
        "We can provide client references upon request with advance notice and client consent."
    ),

    # ── SATISFACTION GUARANTEE / LEGAL POSITIONS ─────────────────────────────
    # Source: Crunch Fitness RFP response (Section 5.9), verified 2026
    "satisfaction_guarantee": (
        "CustomInk delivers high-quality products that match what was created on our site. "
        "We stand behind our work. If for any reason a client is not satisfied, we will "
        "reprint or issue a credit. We do not accept penalty/liquidated damages clauses or "
        "vendor allowance requirements — our Satisfaction Guarantee covers defects and "
        "quality issues comprehensively."
    ),

    # ── PRODUCT CATALOG ──────────────────────────────────────────────────────
    "product_catalog_reference": (
        "CustomInk's catalog includes 6,000+ products across apparel, promotional products, "
        "and awards/trophies. Full catalog: https://www.customink.com/products. "
        "We partner with all major brands including Nike, The North Face, Yeti, Stanley, "
        "Hydro Flask, Comfort Colors, Bella+Canvas, Cotopaxi, Dagne Dover, Under Armour, "
        "Columbia, adidas, Reebok, and more."
    ),
}
