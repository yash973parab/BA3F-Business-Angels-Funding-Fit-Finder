"""
TheBlueprintSchema = THE DATA SHAPE
schema.py — The "form template" the AI must fill in for every investor bio.

Think of this as a structured questionnaire: for each of the 5 dimensions
from the thesis, the AI must pick one type, quote the exact sentence that
proves it, and rate how confident it is. Then it produces a founder-facing
fit signal.

Why this matters (plain terms): without this template, an AI just writes a
paragraph of opinion. With it, every result comes back in the SAME shape,
so the app can reliably display it in cards, and you (or an interviewer)
can check exactly which sentence in the bio led to which conclusion.


schema.py (v2) — The form template, corrected for two things:
1. Each dimension can carry MULTIPLE independent tags (not one exclusive label),
   because your thesis layers separate sub-frameworks within a dimension.
2. A separate "Behavior Profile" block scores the angel on 3 intensity scales
   (Risk Tolerance, Syndication Tendency, Geographic/Sectoral Flexibility),
   1-5, which the app will later draw as colored bars.
"""

from pydantic import BaseModel, Field
from typing import Literal, List

Confidence = Literal["High", "Medium", "Low"]

class Tag(BaseModel):
    """One independent label within a dimension, e.g. 'Super Angel' or 'Analytical Investor'."""
    label: str = Field(..., description="The specific sub-type name, taken from the fixed list for that lens.")
    evidence_quote: str = Field(..., description="Exact phrase from the bio supporting this. If none, write 'No direct evidence in text'.")
    confidence: Confidence

class ExperienceDimension(BaseModel):
    """Two independent lenses: how much they've invested, and how they operate."""
    activity_level: Tag = Field(..., description="One of: Nascent Angel, Novice Angel, Experienced Angel, Super Angel")
    competence_type: Tag = Field(..., description="One of: Lotto Investor, Trader, Analytical Investor, Pure Business Angel, Unclear")

class PsychologyDimension(BaseModel):
    """Three independent lenses: personality traits, cognitive style, and (rarely) ego-driven traits."""
    dominant_traits: List[Tag] = Field(..., description="0-3 tags from: High Extraversion, High Conscientiousness, High Openness, High Agreeableness, Ego-Driven/Narcissistic markers")
    cognitive_style: Tag = Field(..., description="One of: Intuitive / Gut-feel, Analytical / Metrics-driven, Balanced or Unclear")

class InvestmentStyleDimension(BaseModel):
    stage_focus: Tag = Field(..., description="One of: Entrepreneur Angel (early-stage, passion-driven), Wealth-Maximizing Angel (later-stage, ROI-driven), Unclear")
    sector_focus: Tag = Field(..., description="Named sector if stated, e.g. Technology Angel, Healthcare-focused, Sector-agnostic")
    geographic_radius: Tag = Field(..., description="One of: Local/regional preference, Long-distance/no restriction, Unclear")

class OrganizationDimension(BaseModel):
    org_form: Tag = Field(..., description="One of: Solo/Independent Angel, Business Angel Network member, Syndicate member, Unclear")
    network_position: Tag = Field(..., description="One of: Central/well-connected node, Peripheral member, Unclear")

class DemographicsDimension(BaseModel):
    education_background: Tag = Field(..., description="One of: STEM, Business, Finance, Technical/Engineering, Healthcare, Other, Unclear")

class BehaviorProfile(BaseModel):
    """
    The 3 founder-facing behavior scores, derived from the typology tags above
    using the behavioral links documented in Chapter 5 of the thesis.
    Score scale: 1 = very low intensity, 5 = very high intensity.
    """
    risk_tolerance: int = Field(..., ge=1, le=5)
    risk_tolerance_reason: str
    syndication_tendency: int = Field(..., ge=1, le=5, description="How likely this angel is to co-invest with others rather than invest solo.")
    syndication_tendency_reason: str
    geo_sector_flexibility: int = Field(..., ge=1, le=5, description="1 = tightly local & single-sector, 5 = geographically and sectorally flexible.")
    geo_sector_flexibility_reason: str

class FitAssessment(BaseModel):
    stage_match: Literal["Strong fit", "Possible fit", "Likely mismatch"]
    priority_signal: Literal["High priority", "Medium priority", "Low priority — proceed with caution"]
    caution_note: str
    pitch_recommendation: str

class AngelProfile(BaseModel):
    demographics: DemographicsDimension
    experience: ExperienceDimension
    psychology: PsychologyDimension
    investment_style: InvestmentStyleDimension
    organization: OrganizationDimension
    behavior_profile: BehaviorProfile
    fit_assessment: FitAssessment