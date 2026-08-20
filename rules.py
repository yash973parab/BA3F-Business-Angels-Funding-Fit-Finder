"""
TheRules = THE LOGIC
rules.py — Converts the typology tags (extracted by the AI from a bio) into
the 3 behavior scores (Risk Tolerance, Syndication Tendency, Geo/Sector
Flexibility), using fixed point-values sourced directly from Chapter 5 of
the thesis. This is deterministic code, NOT an AI guess — every point is
traceable to a specific finding, which makes the score defensible.

How it works (plain terms): each typology tag nudges each of the 3 scores
up or down by a fixed amount. We add up all the nudges that apply to a
given angel, then squeeze the result into a 1-5 scale.
"""

# Each entry: tag_label -> (risk_nudge, syndication_nudge, flexibility_nudge, source_note)
RULES = {
    # --- Experience: activity level ---
    "Nascent Angel":        (-1, -1, +1, "Nascent/Novice angels rely on availability heuristics -> risk-averse; ~38% report no geographic restrictions; typically withdraw from syndicates (low extraversion in this group)."),
    "Novice Angel":         (-1, -1, +1, "Same pattern as Nascent: risk-averse, low syndication sophistication, few geographic restrictions."),
    "Experienced Angel":    (+1, +1, -1, "Experienced angels rely on representativeness cues -> more risk-tolerant; syndication sophistication increases with experience; more likely to invest locally."),
    "Super Angel":          (+1, +2, 0,  "Super Angels lead syndicates and diversify sectors due to accumulated capital, but are also aware of the benefits of investing close to home."),

    # --- Experience: competence type ---
    "Lotto Investor":       (0, 0, +1, "Lower competence angels scatter across sectors."),
    "Trader":               (0, 0, +1, "Traders are opportunistic across deals and sectors."),
    "Analytical Investor":  (+1, 0, -1, "High competence + calculative risk-taking; selective (not extensive) in group investment; invests within expertise domain -> narrower sector focus, but frequent in long-distance deals via expertise transfer."),
    "Pure Business Angel":  (+1, +2, -1, "High competence, calculative risk-taking, syndicates extensively, invests within expertise domain."),

    # --- Psychology: personality traits ---
    "High Extraversion":       (0, +2, 0, "A one-unit increase in extraversion increases odds of syndication by ~39% (Block et al., 2019)."),
    "High Conscientiousness":  (0, -2, 0, "A one-unit increase in conscientiousness decreases odds of syndication by ~27% (Block et al., 2019); values autonomy and personal due diligence."),
    "High Openness":           (0, +1, +1, "Higher cognitive flexibility theoretically facilitates syndication and broader focus."),
    "High Agreeableness":      (-1, +1, 0, "Agreeableness decreases risk via trust/relationship emphasis over pure financial metrics; eases into collaborative/group investing."),
    "Ego-Driven/Narcissistic markers": (+1, -1, 0, "Ego-driven angels tend toward independent, self-directed decisions over shared credit."),

    # --- Psychology: cognitive style ---
    "Intuitive / Gut-feel":            (+1, -1, +1, "Intuitive angels show higher risk propensity, are comfortable with solo decisions, and may invest long-distance based on founder assessment alone."),
    "Analytical / Metrics-driven":     (-1, +1, -1, "Analytical angels demand quantifiable risk metrics, leverage syndicates to offset information asymmetry, and favor proximity for data access."),

    # --- Investment style: stage focus ---
    "Entrepreneur Angel (early-stage, passion-driven)":     (+1, 0, 0, "Entrepreneur angels show elevated risk-taking driven by passion; no direct syndication or geographic effect documented."),
    "Wealth-Maximizing Angel (later-stage, ROI-driven)":     (+1, +1, 0, "Wealth-maximizing angels also show elevated risk-taking (seeking proportionately higher returns) and resemble institutional VCs with elevated syndicate affinity."),

    # --- Investment style: sector focus ---
    "Technology Angel":     (0, 0, +1, "Industry-specific (esp. tech) affinity is associated with willingness to invest long-distance, pushing geographic boundaries for the right sector fit."),

    # --- Organization: form ---
    "Solo/Independent Angel":            (+1, -2, -1, "Solo angels show higher risk acceptance (no group due-diligence curtailing risk); organizational form directly determines (low) syndication."),
    "Business Angel Network member":     (-1, +2, +1, "BANs/formal groups curtail individual risk via due diligence; network membership enables geographic reach beyond individual capacity; varied member backgrounds support sector diversity."),
    "Syndicate member":                  (-1, +2, +1, "Syndication is by definition co-investing; pooled expertise from varied backgrounds supports broader sector reach."),

    # --- Organization: network position ---
    "Central/well-connected node":  (0, +1, 0, "Central angels are far more inclined toward syndication than peripheral members; they often initiate deals and recruit co-investors."),
    "Peripheral member":            (0, -1, 0, "Peripheral members tend to join existing syndicates rather than lead, and rely on central angels' screening."),
}

def score_behavior_profile(tags: list[str]) -> dict:
    """
    tags: list of typology label strings extracted from the bio (e.g.
          ["Super Angel", "Analytical Investor", "High Conscientiousness", ...])
    Returns the 3 scores (1-5) plus the list of reasons that contributed.
    """
    risk, synd, flex = 0, 0, 0
    reasons = []
    for tag in tags:
        if tag in RULES:
            r, s, f, note = RULES[tag]
            risk += r
            synd += s
            flex += f
            if r or s or f:
                reasons.append(f"{tag}: {note}")

    def squeeze(raw_sum):
        # baseline of 3 (neutral), then nudge, then clip to 1-5
        return max(1, min(5, 3 + round(raw_sum / 2)))

    return {
        "risk_tolerance": squeeze(risk),
        "syndication_tendency": squeeze(synd),
        "geo_sector_flexibility": squeeze(flex),
        "contributing_reasons": reasons
    }