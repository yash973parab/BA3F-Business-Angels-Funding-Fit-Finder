"""
extractor.py — The AI instructions (the "prompt") that reads an investor
bio and fills out the schema.py form, using definitions taken directly
from the thesis. rules.py then converts the tags into behavior scores.

CURRENTLY ACTIVE: Google Gemini (free tier, no cost).
KEPT ON STANDBY: Claude/Anthropic (commented out below).

WHAT YOU NEED FOR GEMINI (currently active):
1. A FREE Google Gemini API key — go to aistudio.google.com, sign in
   with any Google account, click "Get API key". No credit card needed.
2. Save it as an environment variable named GEMINI_API_KEY.
3. Run: pip install google-genai pydantic

NOTE (Aug 2026): Google periodically retires older model names. If you
ever get a 404 "model no longer available" error again, check
ai.google.dev/gemini-api/docs/models for the current free Flash model
name and update MODEL_NAME below — nothing else needs to change.

Until you add a key, this file runs in MOCK MODE (fake but structurally
correct output) so you can see the full pipeline working end-to-end.
"""

from schema import AngelProfile
from rules import score_behavior_profile

# Update this single constant if Google retires the model name again.
MODEL_NAME = "gemini-3.6-flash"

# -----------------------------------------------------------------------
# STEP 1: The knowledge the AI is given (taken directly from your thesis)
# -----------------------------------------------------------------------
TAXONOMY_DEFINITIONS = """
You are classifying a business angel investor based on their public bio text,
using a typology framework from academic entrepreneurial finance research.
Use ONLY evidence present in the bio text. If a dimension has no evidence,
mark it "Unclear" and confidence "Low" — do NOT invent evidence.

DIMENSION 1 - EXPERIENCE (two independent lenses):
 Activity level: Nascent Angel (no deals yet) | Novice Angel (few deals) |
   Experienced Angel (multiple deals, track record) | Super Angel (large
   number of deals, often leads syndicates, high capital deployed).
 Competence type: Lotto Investor (invests opportunistically, little
   diligence) | Trader (opportunistic, deal-focused) | Analytical Investor
   (rigorous, metrics-driven, selective) | Pure Business Angel (high
   competence, extensive syndication, deep sector expertise).

DIMENSION 2 - PSYCHOLOGY (two independent lenses):
 Dominant traits (pick 0-3 only if clearly evidenced): High Extraversion
   (socially active, network-driven language) | High Conscientiousness
   (emphasis on discipline, personal due diligence, autonomy) | High
   Openness (mentions of flexibility, novel ideas, broad curiosity) |
   High Agreeableness (emphasis on trust, relationships, collaboration) |
   Ego-Driven/Narcissistic markers (self-promotional language, credit-seeking).
 Cognitive style: Intuitive/Gut-feel (decisions based on founder impression,
   passion, pattern recognition) | Analytical/Metrics-driven (demands data,
   financial models, quantifiable proof) | Balanced or Unclear.

DIMENSION 3 - INVESTMENT STYLE (three independent lenses):
 Stage focus: Entrepreneur Angel (early-stage/seed, passion-driven,
   often former founders) | Wealth-Maximizing Angel (later-stage, ROI and
   return-focused, resembles institutional VC behavior).
 Sector focus: name the specific sector if stated (e.g. "Technology Angel",
   "Healthcare-focused") or "Sector-agnostic" if diversified/unstated.
 Geographic radius: Local/regional preference (explicitly mentions local
   investing) | Long-distance/no restriction (mentions investing across
   regions/countries) | Unclear.

DIMENSION 4 - ORGANIZATION (two independent lenses):
 Organizational form: Solo/Independent Angel (invests alone) | Business
   Angel Network member (part of a formal angel network/BAN) | Syndicate
   member (regularly co-invests with a specific group).
 Network position: Central/well-connected node (leads deals, recruits
   co-investors, described as influential/connector) | Peripheral member
   (joins others' deals, less deal-leading language) | Unclear.

DIMENSION 5 - DEMOGRAPHICS:
 Education background: STEM | Business | Finance | Technical/Engineering |
   Healthcare | Other | Unclear.

For EVERY tag you assign, you must quote the exact phrase from the bio that
justifies it, and rate your confidence (High/Medium/Low). If evidence is
indirect or you are inferring, use Medium or Low, never High.
"""

# -----------------------------------------------------------------------
# STEP 2: Worked examples (few-shot) — anchors the AI's judgment
# -----------------------------------------------------------------------
FEW_SHOT_EXAMPLES = """
EXAMPLE BIO 1:
"Maria has invested in over 30 startups since 2010, primarily in fintech
and healthtech. She rarely invests alone, preferring to co-lead syndicates
with a close group of fellow angels. Known in her network for rigorous
financial modeling before committing, she has said 'I don't invest on gut
feel, I invest on unit economics.'"

EXPECTED READING: Activity level = Super Angel (30+ investments, "since 2010").
Competence type = Analytical Investor ("rigorous financial modeling").
Cognitive style = Analytical/Metrics-driven (direct quote). Organizational
form = Syndicate member ("co-lead syndicates"). Network position =
Central/well-connected node ("co-lead", "known in her network"). Sector
focus = leaning fintech/healthtech (state both). Stage focus = Unclear
(not stated).

EXAMPLE BIO 2:
"John made his money in real estate and now enjoys backing first-time
founders he believes in, especially those building something he wishes
existed when he was starting out. He typically writes the first check
and decides fast, often within a single coffee meeting."

EXPECTED READING: Stage focus = Entrepreneur Angel ("first-time founders",
"first check", relives founding experience). Cognitive style =
Intuitive/Gut-feel ("decides fast", "within a single coffee meeting").
Organizational form = Solo/Independent Angel (no mention of co-investors,
"he typically writes the first check" implies solo decision). Activity
level = Unclear (no deal count given at all).
"""

SYSTEM_PROMPT = TAXONOMY_DEFINITIONS + "\n\n" + FEW_SHOT_EXAMPLES


def _tags_from_profile(profile: AngelProfile) -> list[str]:
    """Pulls out all the labels the AI assigned, so rules.py can score them."""
    return [
        profile.experience.activity_level.label,
        profile.experience.competence_type.label,
        profile.psychology.cognitive_style.label,
    ] + [t.label for t in profile.psychology.dominant_traits] + [
        profile.investment_style.stage_focus.label,
        profile.investment_style.sector_focus.label,
        profile.organization.org_form.label,
        profile.organization.network_position.label,
    ]


# -----------------------------------------------------------------------
# STEP 3: The actual function the app will call
# -----------------------------------------------------------------------
def classify_bio(bio_text: str, founder_stage: str, founder_sector: str, mock: bool = True) -> dict:
    """
    bio_text: the investor bio pasted by the founder
    founder_stage: e.g. "Pre-seed", "Seed", "Series A"
    founder_sector: e.g. "Automotive", "SaaS"
    mock: if True, skips the real API call and returns a structurally
          correct fake result (for testing before you have an API key)
    """
    user_prompt = f"""
Bio to classify:
\"\"\"{bio_text}\"\"\"

Founder's current stage: {founder_stage}
Founder's sector: {founder_sector}

Fill out the AngelProfile form completely, following the definitions and
examples given. Also fill fit_assessment: compare the angel's likely stage
focus to the founder's stage ({founder_stage}) to set stage_match,
priority_signal, caution_note, and pitch_recommendation.
"""

    if mock:
        raw_tags = ["Super Angel", "Analytical Investor", "High Conscientiousness",
                    "Analytical / Metrics-driven", "Syndicate member",
                    "Central/well-connected node"]
        behavior = score_behavior_profile(raw_tags)
        return {
            "mode": "MOCK (no real API call made)",
            "extracted_tags": raw_tags,
            "behavior_profile": behavior,
            "note": "Once your GEMINI_API_KEY is set, mock=False will call the real (free) Gemini model."
        }

    # =====================================================================
    # ACTIVE IMPLEMENTATION: Google Gemini (free tier)
    # =====================================================================
    from google import genai

    client = genai.Client()  # reads GEMINI_API_KEY from environment automatically

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": AngelProfile,
        },
    )

    profile: AngelProfile = response.parsed
    behavior = score_behavior_profile(_tags_from_profile(profile))

    return {
        "mode": "LIVE (Gemini, free tier)",
        "profile": profile.model_dump(),
        "behavior_profile": behavior
    }

    # =====================================================================
    # STANDBY IMPLEMENTATION: Claude / Anthropic (commented out)
    # -------------------------------------------------------------------
    # To switch to this later:
    #   1. Comment out the entire Gemini block above (from
    #      "from google import genai" down to the "return" just above
    #      this comment).
    #   2. Uncomment the block below.
    #   3. pip install anthropic
    #   4. Set ANTHROPIC_API_KEY as an environment variable (paid — small
    #      pay-as-you-go cost, no permanent free tier as of Aug 2026).
    # =====================================================================
    #
    # from anthropic import Anthropic
    # client = Anthropic()  # reads ANTHROPIC_API_KEY from environment automatically
    #
    # angel_profile_schema = AngelProfile.model_json_schema()
    #
    # response = client.messages.create(
    #     model="claude-sonnet-4-5-20250929",
    #     max_tokens=2000,
    #     system=SYSTEM_PROMPT,
    #     tools=[{
    #         "name": "fill_angel_profile",
    #         "description": "Fill out the structured AngelProfile classification form for the given bio.",
    #         "input_schema": angel_profile_schema,
    #     }],
    #     tool_choice={"type": "tool", "name": "fill_angel_profile"},
    #     messages=[{"role": "user", "content": user_prompt}],
    # )
    #
    # tool_call = next(block for block in response.content if block.type == "tool_use")
    # profile = AngelProfile.model_validate(tool_call.input)
    # behavior = score_behavior_profile(_tags_from_profile(profile))
    #
    # return {
    #     "mode": "LIVE (Claude)",
    #     "profile": profile.model_dump(),
    #     "behavior_profile": behavior
    # }