import re

def analyze_pitch(name: str, sector: str, stage: str, description: str, treatment_plan: str) -> dict:
    """
    Local heuristic-based business pitch analyzer that returns scores, strengths, gaps, and roadmap steps.
    """
    score = 55  # Base score
    
    # 1. Length validation metrics
    desc_len = len(description.strip())
    plan_len = len(treatment_plan.strip())
    
    if desc_len > 200:
        score += 12
    elif desc_len > 100:
        score += 6
    elif desc_len < 30:
        score -= 15

    if plan_len > 500:
        score += 15
    elif plan_len > 250:
        score += 8
    elif plan_len < 50:
        score -= 15

    # 2. Key operational terms matching
    keywords = [
        "revenue", "saas", "api", "growth", "margin", "patent", "database",
        "retention", "acquisition", "pipeline", "scalability", "leverage",
        "infrastructure", "automation", "compliance", "encryption", "custom"
    ]
    
    matches_found = 0
    text_corpus = (description + " " + treatment_plan).lower()
    for kw in keywords:
        if kw in text_corpus:
            score += 3
            matches_found += 1
            if matches_found >= 6:  # Cap keyword bonuses
                break

    # 3. Financial representation checks
    # Look for Indian Rupees symbol (₹), dollars ($), or metrics like Lakhs (L), Crores (Cr), or numbers
    financial_pat = r"(₹|\$|\bL\b|\bLakh\b|\bCr\b|\bCrore\b|\bUSD\b|\d+%)"
    if re.search(financial_pat, text_corpus):
        score += 10

    # 4. Dev Stage multipliers
    stage_upper = stage.upper().strip()
    if "REVENUE" in stage_upper:
        score += 10
    elif "MVP" in stage_upper:
        score += 6
    elif "PROTOTYPE" in stage_upper:
        score += 3
    elif "IDEA" in stage_upper:
        score -= 2

    # Clamp the final score between 10 and 100
    score = max(10, min(100, score))
    
    # Determine qualitative grade letter
    if score >= 85:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 50:
        grade = "C"
    else:
        grade = "D"

    # Assemble contextual strengths
    strengths = []
    if plan_len > 350:
        strengths.append("High-quality, detailed solution architecture and execution roadmap.")
    if matches_found >= 4:
        strengths.append("Strong business taxonomy featuring clear scalability and monetization triggers.")
    if re.search(financial_pat, text_corpus):
        strengths.append("Includes clear financial parameters or target check expectations.")
    if len(strengths) == 0:
        strengths.append("Initial idea registered successfully. Ready for refinement.")

    # Assemble gaps and risks
    gaps = []
    if plan_len < 150:
        gaps.append("The implementation plan is brief. Provide more engineering details to build investor confidence.")
    if matches_found < 3:
        gaps.append("Lacks specific monetization or distribution keywords (SaaS, retention, etc.).")
    if not re.search(financial_pat, text_corpus):
        gaps.append("No financial projections or funding requirements mentioned in the pitch text.")
    if len(gaps) == 0:
        gaps.append("No critical information gaps identified in the submission draft.")

    # Custom roadmap steps
    roadmap = [
        "Complete secure cryptographic vault registration.",
        "Refine target customer persona and distribution parameters."
    ]
    if plan_len < 300:
        roadmap.append("Flesh out implementation steps to exceed 400 characters of solutions text.")
    if not re.search(financial_pat, text_corpus):
        roadmap.append("Define specific budget allocations and check targets.")
    if stage_upper == "IDEA":
        roadmap.append("Construct initial prototype using reusable components from the failed startup asset list.")
    else:
        roadmap.append("Verify customer KYC profiles to set up direct deal rooms.")

    return {
        "score": score,
        "grade": grade,
        "strengths": strengths,
        "gaps": gaps,
        "roadmap": roadmap
    }
