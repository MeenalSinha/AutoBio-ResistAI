"""
treatment.py
------------
Evidence-based antibiotic treatment recommendation module.
Maps resistance predictions and detected resistance genes to actionable
antibiotic stewardship recommendations.
"""

from typing import Dict, List, Any, Optional


# ---------------------------------------------------------------------------
# Antibiotic class taxonomy
# ---------------------------------------------------------------------------

ANTIBIOTIC_CLASSES = {
    # Beta-lactams
    "Ampicillin":           "Beta-lactam (Aminopenicillin)",
    "Amoxicillin":          "Beta-lactam (Aminopenicillin)",
    "Penicillin":           "Beta-lactam (Natural penicillin)",
    "Oxacillin":            "Beta-lactam (Antistaphylococcal penicillin)",
    "Ceftriaxone":          "Beta-lactam (3rd-gen Cephalosporin)",
    "Cefazolin":            "Beta-lactam (1st-gen Cephalosporin)",
    "Cefepime":             "Beta-lactam (4th-gen Cephalosporin)",
    "Meropenem":            "Carbapenem",
    "Imipenem":             "Carbapenem",
    "Ertapenem":            "Carbapenem",
    "Piperacillin-Tazobactam": "Beta-lactam + Beta-lactamase inhibitor",
    "Amoxicillin-Clavulanate": "Beta-lactam + Beta-lactamase inhibitor",
    # Fluoroquinolones
    "Ciprofloxacin":        "Fluoroquinolone",
    "Levofloxacin":         "Fluoroquinolone",
    "Moxifloxacin":         "Fluoroquinolone",
    # Aminoglycosides
    "Gentamicin":           "Aminoglycoside",
    "Amikacin":             "Aminoglycoside",
    "Tobramycin":           "Aminoglycoside",
    # Tetracyclines
    "Tetracycline":         "Tetracycline",
    "Doxycycline":          "Tetracycline",
    "Tigecycline":          "Glycylcycline (Tetracycline class)",
    # Macrolides
    "Azithromycin":         "Macrolide",
    "Erythromycin":         "Macrolide",
    "Clarithromycin":       "Macrolide",
    # Glycopeptides
    "Vancomycin":           "Glycopeptide",
    "Teicoplanin":          "Glycopeptide",
    # Others
    "Chloramphenicol":      "Phenicol",
    "Trimethoprim":         "Diaminopyrimidine",
    "Trimethoprim-Sulfamethoxazole": "Sulfonamide combination",
    "Colistin":             "Polymyxin",
    "Linezolid":            "Oxazolidinone",
    "Daptomycin":           "Lipopeptide",
    "Rifampicin":           "Rifamycin",
    "Clindamycin":          "Lincosamide",
    "Metronidazole":        "Nitroimidazole",
    "Fosfomycin":           "Phosphonic acid",
    "Nitrofurantoin":       "Nitrofuran",
}


# ---------------------------------------------------------------------------
# Resistance gene → affected drugs
# ---------------------------------------------------------------------------

GENE_RESISTANCE_MAP = {
    "gene_blatem":  ["Ampicillin", "Amoxicillin", "Penicillin", "Cefazolin"],
    "gene_meca":    ["Oxacillin", "Ampicillin", "Penicillin", "Cefazolin",
                     "Ceftriaxone", "Amoxicillin-Clavulanate"],
    "gene_vana":    ["Vancomycin", "Teicoplanin"],
    "gene_qnrs":    ["Ciprofloxacin", "Levofloxacin", "Moxifloxacin"],
    "gene_arma":    ["Gentamicin", "Amikacin", "Tobramycin"],
}

# ---------------------------------------------------------------------------
# Species-specific first-line options
# ---------------------------------------------------------------------------

SPECIES_RECOMMENDATIONS: Dict[str, Dict[str, List[str]]] = {
    "E. coli": {
        "first_line":    ["Trimethoprim-Sulfamethoxazole", "Nitrofurantoin", "Ciprofloxacin"],
        "alternative":   ["Ceftriaxone", "Amikacin", "Meropenem", "Fosfomycin"],
        "last_resort":   ["Colistin", "Tigecycline"],
    },
    "K. pneumoniae": {
        "first_line":    ["Ceftriaxone", "Gentamicin", "Ciprofloxacin"],
        "alternative":   ["Meropenem", "Piperacillin-Tazobactam", "Amikacin"],
        "last_resort":   ["Colistin", "Tigecycline"],
    },
    "S. aureus": {
        "first_line":    ["Cefazolin", "Oxacillin", "Clindamycin"],
        "alternative":   ["Vancomycin", "Linezolid", "Daptomycin"],
        "last_resort":   ["Daptomycin", "Linezolid", "Teicoplanin"],
    },
    "P. aeruginosa": {
        "first_line":    ["Piperacillin-Tazobactam", "Cefepime", "Ciprofloxacin"],
        "alternative":   ["Meropenem", "Amikacin", "Tobramycin"],
        "last_resort":   ["Colistin", "Fosfomycin"],
    },
    "A. baumannii": {
        "first_line":    ["Meropenem", "Imipenem", "Ampicillin-Sulbactam"],
        "alternative":   ["Tigecycline", "Colistin"],
        "last_resort":   ["Colistin", "Rifampicin"],
    },
}

DEFAULT_RECOMMENDATIONS = {
    "first_line":  ["Amoxicillin-Clavulanate", "Ciprofloxacin", "Trimethoprim-Sulfamethoxazole"],
    "alternative": ["Ceftriaxone", "Gentamicin", "Meropenem"],
    "last_resort": ["Colistin", "Linezolid", "Tigecycline"],
}

# Drugs that should be explicitly avoided for Last Resort if primary lines work
AVOID_UNLESS_NECESSARY = ["Colistin", "Tigecycline"]


# ---------------------------------------------------------------------------
# Main recommendation function
# ---------------------------------------------------------------------------

def recommend_treatment(
    prediction: str,
    species: Optional[str] = None,
    detected_genes: Optional[List[str]] = None,
    shap_top_features: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Generate treatment recommendations based on:
      - resistance prediction (Resistant / Susceptible / Intermediate)
      - bacterial species (if known)
      - resistance genes detected (if available)

    Returns a structured recommendation dict.
    """
    detected_genes = detected_genes or []
    shap_top_features = shap_top_features or []

    # Normalise inputs
    prediction = prediction.strip().capitalize()
    species_key = _normalise_species(species) if species else None

    # Identify drugs affected by detected genes
    gene_affected_drugs = _get_gene_affected_drugs(detected_genes, shap_top_features)

    # Fetch species-specific recommendations
    base_recs = SPECIES_RECOMMENDATIONS.get(species_key, DEFAULT_RECOMMENDATIONS) if species_key else DEFAULT_RECOMMENDATIONS

    if prediction == "Susceptible":
        return _susceptible_recommendation(base_recs, gene_affected_drugs, species_key)
    elif prediction == "Resistant":
        return _resistant_recommendation(base_recs, gene_affected_drugs, species_key, detected_genes)
    else:  # Intermediate
        return _intermediate_recommendation(base_recs, gene_affected_drugs, species_key)


# ---------------------------------------------------------------------------
# Branch builders
# ---------------------------------------------------------------------------

def _susceptible_recommendation(base, gene_affected, species) -> Dict[str, Any]:
    available = [d for d in base["first_line"] if d not in gene_affected]
    return {
        "status":     "Susceptible",
        "urgency":    "Standard",
        "primary_recommendations": available or base["first_line"],
        "alternative_recommendations": base["alternative"],
        "drugs_to_avoid": gene_affected,
        "clinical_notes": [
            "Standard first-line therapy is expected to be effective.",
            "Complete the full course of antibiotics to prevent resistance development.",
            "Monitor clinical response within 48-72 hours.",
            "Perform culture sensitivity testing to confirm susceptibility.",
        ],
        "stewardship_note": (
            "This isolate appears susceptible. Use the narrowest-spectrum agent "
            "appropriate for the infection site to preserve broader options."
        ),
        "mechanism_notes": _gene_mechanism_notes(gene_affected),
    }


def _resistant_recommendation(base, gene_affected, species, genes) -> Dict[str, Any]:
    # Filter alternatives, avoiding affected drugs
    alts = [d for d in base["alternative"] if d not in gene_affected]
    last_resort = base["last_resort"]

    notes = [
        "Standard first-line antibiotics are likely ineffective for this isolate.",
        "Initiate alternative therapy as soon as susceptibility results are confirmed.",
        "Consult infectious disease specialists for multi-drug resistant (MDR) cases.",
        "Review infection control protocols to prevent nosocomial spread.",
    ]
    if any("carbapenem" in ANTIBIOTIC_CLASSES.get(d, "").lower() for d in gene_affected):
        notes.append("Carbapenem resistance detected — suspect carbapenemase-producing organism (CPO). Notify infection control.")

    return {
        "status":     "Resistant",
        "urgency":    "High — seek specialist input",
        "primary_recommendations": alts or base["alternative"],
        "last_resort_options":     last_resort,
        "drugs_to_avoid":          list(set(gene_affected + base.get("first_line", []))),
        "clinical_notes":          notes,
        "stewardship_note": (
            "This isolate is resistant. Avoid empiric broad-spectrum therapy without "
            "susceptibility data. Consider combination therapy only under specialist guidance."
        ),
        "mechanism_notes": _gene_mechanism_notes(genes),
        "resistance_genes_detected": genes,
    }


def _intermediate_recommendation(base, gene_affected, species) -> Dict[str, Any]:
    return {
        "status":     "Intermediate",
        "urgency":    "Moderate — close monitoring required",
        "primary_recommendations": base["first_line"],
        "alternative_recommendations": base["alternative"],
        "drugs_to_avoid": gene_affected,
        "clinical_notes": [
            "Intermediate susceptibility: treatment may succeed with optimised dosing.",
            "Consider higher doses or continuous infusion for beta-lactams (PK/PD optimisation).",
            "Repeat susceptibility testing is recommended.",
            "Monitor patient closely for therapeutic failure.",
        ],
        "stewardship_note": (
            "Intermediate results require careful clinical judgement. "
            "Consult a pharmacist for dose optimisation strategies."
        ),
        "mechanism_notes": _gene_mechanism_notes(gene_affected),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_species(species: str) -> Optional[str]:
    """Fuzzy-match a species name to our recommendation keys."""
    if not species:
        return None
    lower = species.lower()
    for key in SPECIES_RECOMMENDATIONS:
        if key.lower() in lower or lower in key.lower():
            return key
    return None


def _get_gene_affected_drugs(genes: List[str], shap_features: List[Dict]) -> List[str]:
    affected = set()
    for gene in genes:
        lower_gene = gene.lower()
        for gene_key, drugs in GENE_RESISTANCE_MAP.items():
            if gene_key in lower_gene or lower_gene in gene_key:
                affected.update(drugs)

    # Also check SHAP top features for gene signatures
    for feat in shap_features:
        fname = feat.get("feature", "").lower()
        for gene_key, drugs in GENE_RESISTANCE_MAP.items():
            if gene_key in fname:
                affected.update(drugs)

    return list(affected)


def _gene_mechanism_notes(genes: List[str]) -> List[str]:
    notes = []
    for gene in genes:
        lower = gene.lower()
        if "blatem" in lower or "bla" in lower:
            notes.append("Beta-lactamase detected: beta-lactam antibiotics may be hydrolysed. Consider beta-lactamase inhibitor combinations.")
        if "meca" in lower:
            notes.append("mecA detected (MRSA marker): all beta-lactams except ceftaroline should be avoided.")
        if "vana" in lower:
            notes.append("vanA detected: glycopeptide (vancomycin/teicoplanin) resistance. Use linezolid or daptomycin.")
        if "qnr" in lower:
            notes.append("Plasmid-mediated quinolone resistance (PMQR): fluoroquinolone MIC elevation expected.")
        if "arma" in lower:
            notes.append("16S rRNA methylase detected: pan-aminoglycoside resistance. Avoid entire aminoglycoside class.")
    return notes
