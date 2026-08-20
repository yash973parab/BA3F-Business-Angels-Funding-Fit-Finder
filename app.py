"""
app.py — The Streamlit screen a founder actually sees and uses.

WHAT THIS FILE DOES (plain terms):
1. Shows a text box for the founder to paste an investor bio.
2. Asks two quick questions: what stage is your startup at, and what sector.
3. On clicking "Analyze", it calls extractor.py (which either fakes a result
   in MOCK mode, or calls the real free Gemini model in LIVE mode).
4. Displays the 5-dimension classification as simple cards (type + quote +
   confidence), the 3 behavior scores as colored bars, and the fit
   assessment (with the caution note) as a highlighted box at the top.

HOW TO RUN THIS (once all 4 files are saved in the same folder):
    Open a terminal in that folder and type:  streamlit run app.py
    A browser tab will open automatically with the app.
"""

import streamlit as st
from extractor import classify_bio

st.set_page_config(page_title="Angel Investor Fit Finder", layout="centered")

st.title("Angel Investor Fit Finder")
st.caption(
    "Paste a public investor bio (LinkedIn summary, AngelList profile, "
    "pitch-feedback email, etc.) to see their likely investing type and "
    "whether they're a good fit for your pitch — based on a business angel "
    "typology framework from academic research."
)

# -----------------------------------------------------------------------
# INPUTS
# -----------------------------------------------------------------------
with st.form("bio_form"):
    bio_text = st.text_area(
        "Investor bio text",
        height=180,
        placeholder="Paste the investor's public bio here...",
    )

    col1, col2 = st.columns(2)
    with col1:
        founder_stage = st.selectbox(
            "Your startup's current stage",
            ["Pre-seed", "Seed", "Series A", "Series B or later"],
        )
    with col2:
        founder_sector = st.text_input(
            "Your startup's sector",
            placeholder="e.g. Automotive, Fintech, HealthTech",
        )

    use_live_mode = st.checkbox(
        "Use real AI (requires a free Gemini API key set up on this machine). "
        "Leave unchecked to see a demo result with no API key needed.",
        value=False,
    )

    submitted = st.form_submit_button("Analyze this investor")

# -----------------------------------------------------------------------
# HELPER: colored bar for the 3 behavior scores
# -----------------------------------------------------------------------
def colored_bar(label: str, score: int, reason: str):
    pct = int((score / 5) * 100)
    # green (low) -> yellow (mid) -> red (high) gradient by score
    color = ["#2ecc71", "#82c91e", "#f1c40f", "#e67e22", "#e74c3c"][score - 1]
    st.markdown(f"**{label}: {score}/5**")
    st.markdown(
        f"""
        <div style="background-color:#eee; border-radius:6px; height:18px; width:100%;">
          <div style="background-color:{color}; width:{pct}%; height:100%; border-radius:6px;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(reason)
    st.write("")

# -----------------------------------------------------------------------
# HELPER: a small card for one dimension tag
# -----------------------------------------------------------------------
def tag_card(title: str, label: str, quote: str, confidence: str):
    st.markdown(f"**{title}:** {label}  \n*Confidence: {confidence}*")
    st.caption(f"Evidence: \"{quote}\"")

# -----------------------------------------------------------------------
# RUN CLASSIFICATION AND DISPLAY RESULTS
# -----------------------------------------------------------------------
if submitted:
    if not bio_text.strip():
        st.warning("Please paste an investor bio before analyzing.")
    else:
        with st.spinner("Analyzing bio..."):
            result = classify_bio(
                bio_text=bio_text,
                founder_stage=founder_stage,
                founder_sector=founder_sector or "Unspecified",
                mock=not use_live_mode,
            )

        st.divider()
        st.subheader("Result")
        st.caption(f"Mode: {result['mode']}")

        if result["mode"].startswith("MOCK"):
            st.info(
                "This is a demo result (mock mode) — no real AI was called. "
                "Check 'Use real AI' above once your free Gemini API key is set up."
            )
            st.markdown("**Example tags that would be detected:**")
            st.write(", ".join(result["extracted_tags"]))
            bp = result["behavior_profile"]
            st.markdown("### Behavior Profile (demo)")
            colored_bar("Risk Tolerance", bp["risk_tolerance"], "Demo score for illustration.")
            colored_bar("Syndication Tendency", bp["syndication_tendency"], "Demo score for illustration.")
            colored_bar("Geo/Sector Flexibility", bp["geo_sector_flexibility"], "Demo score for illustration.")

        else:
            profile = result["profile"]
            bp = result["behavior_profile"]
            fit = profile["fit_assessment"]

            # --- Fit assessment banner at the top (the founder's bottom line) ---
            priority_color = {
                "High priority": "success",
                "Medium priority": "warning",
                "Low priority — proceed with caution": "error",
            }.get(fit["priority_signal"], "info")

            box = {"success": st.success, "warning": st.warning, "error": st.error}.get(priority_color, st.info)
            box(f"**{fit['stage_match']}** — {fit['priority_signal']}")
            st.markdown(f"**Caution note:** {fit['caution_note']}")
            st.markdown(f"**Pitch recommendation:** {fit['pitch_recommendation']}")

            st.divider()
            st.markdown("### Behavior Profile")
            colored_bar("Risk Tolerance", bp["risk_tolerance"], bp.get("risk_tolerance_reason", ""))
            colored_bar("Syndication Tendency", bp["syndication_tendency"], bp.get("syndication_tendency_reason", ""))
            colored_bar("Geo/Sector Flexibility", bp["geo_sector_flexibility"], bp.get("geo_sector_flexibility_reason", ""))
            if bp.get("contributing_reasons"):
                with st.expander("Why these scores? (source reasoning)"):
                    for r in bp["contributing_reasons"]:
                        st.write("- " + r)

            st.divider()
            st.markdown("### Typology Breakdown")

            tag_card("Education background", profile["demographics"]["education_background"]["label"],
                      profile["demographics"]["education_background"]["evidence_quote"],
                      profile["demographics"]["education_background"]["confidence"])

            st.markdown("**Experience**")
            tag_card("Activity level", profile["experience"]["activity_level"]["label"],
                      profile["experience"]["activity_level"]["evidence_quote"],
                      profile["experience"]["activity_level"]["confidence"])
            tag_card("Competence type", profile["experience"]["competence_type"]["label"],
                      profile["experience"]["competence_type"]["evidence_quote"],
                      profile["experience"]["competence_type"]["confidence"])

            st.markdown("**Psychology**")
            for trait in profile["psychology"]["dominant_traits"]:
                tag_card("Trait", trait["label"], trait["evidence_quote"], trait["confidence"])
            tag_card("Cognitive style", profile["psychology"]["cognitive_style"]["label"],
                      profile["psychology"]["cognitive_style"]["evidence_quote"],
                      profile["psychology"]["cognitive_style"]["confidence"])

            st.markdown("**Investment Style**")
            tag_card("Stage focus", profile["investment_style"]["stage_focus"]["label"],
                      profile["investment_style"]["stage_focus"]["evidence_quote"],
                      profile["investment_style"]["stage_focus"]["confidence"])
            tag_card("Sector focus", profile["investment_style"]["sector_focus"]["label"],
                      profile["investment_style"]["sector_focus"]["evidence_quote"],
                      profile["investment_style"]["sector_focus"]["confidence"])
            tag_card("Geographic radius", profile["investment_style"]["geographic_radius"]["label"],
                      profile["investment_style"]["geographic_radius"]["evidence_quote"],
                      profile["investment_style"]["geographic_radius"]["confidence"])

            st.markdown("**Organization**")
            tag_card("Organizational form", profile["organization"]["org_form"]["label"],
                      profile["organization"]["org_form"]["evidence_quote"],
                      profile["organization"]["org_form"]["confidence"])
            tag_card("Network position", profile["organization"]["network_position"]["label"],
                      profile["organization"]["network_position"]["evidence_quote"],
                      profile["organization"]["network_position"]["confidence"])