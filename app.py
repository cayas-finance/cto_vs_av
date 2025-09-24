from __future__ import annotations

from dataclasses import dataclass

from typing import Optional, Tuple

from flask import Flask, render_template, request

from CTO_vs_AV import (
    calcul_impot_progressif,
    calculer_heritage_assurance_vie,
    calculer_heritage_cto,
    get_regime_successoral,
)


app = Flask(__name__)


@dataclass
class ComparisonResult:
    heritage_av: float
    heritage_cto: float
    heritage_autres_av: float
    heritage_autres_cto: float
    heritage_total_av: float
    heritage_total_cto: float
    capital_final_av: float
    capital_final_cto: float
    patrimoine_total_av: float
    patrimoine_total_cto: float
    part_taxable_av: float
    part_taxable_cto: float
    impots_payes_av: float
    impots_payes_cto: float
    difference_totale: float
    relative_difference: Optional[float]
    base_totale: float


@dataclass
class ScenarioInputs:
    capital_initial: float
    autres_biens_valeur: float
    duree: float
    rendement_annuel: float
    frais_gestion_av: float
    frais_sociaux_av: float
    nb_heriters: int
    nb_beneficiaires: int
    lien: str
    versements_av_avant70: bool


def compute_comparison(inputs: ScenarioInputs) -> Tuple[ComparisonResult, dict]:
    abattement_par_heritier, bareme_succession = get_regime_successoral(inputs.lien)
    abattement_succession_total = abattement_par_heritier * inputs.nb_heriters

    if inputs.versements_av_avant70:
        abattement_av = 152_500
        bareme_av = [(700_000, 0.20), (float("inf"), 0.3125)]
    else:
        abattement_av = 30_500
        bareme_av = [(float("inf"), 0.0)]

    abattement_fiscal_av_total = abattement_av * inputs.nb_beneficiaires

    heritage_av, capital_final_av = calculer_heritage_assurance_vie(
        inputs.capital_initial,
        inputs.duree,
        inputs.rendement_annuel,
        inputs.frais_gestion_av,
        inputs.frais_sociaux_av,
        abattement_fiscal_av_total,
        bareme_av,
    )

    base_autres_biens_av = max(0.0, inputs.autres_biens_valeur - abattement_succession_total)
    droits_autres_biens_av = calcul_impot_progressif(base_autres_biens_av, bareme_succession)
    heritage_autres_av = inputs.autres_biens_valeur - droits_autres_biens_av
    heritage_total_av = heritage_av + heritage_autres_av
    patrimoine_total_av = capital_final_av + inputs.autres_biens_valeur

    heritage_cto, capital_final_cto = calculer_heritage_cto(
        inputs.capital_initial,
        inputs.duree,
        inputs.rendement_annuel,
        inputs.autres_biens_valeur,
        abattement_succession_total,
        bareme_succession,
    )

    actif_total_cto = capital_final_cto + inputs.autres_biens_valeur
    base_imposable_totale = max(0.0, actif_total_cto - abattement_succession_total)
    droits_totaux_cto = calcul_impot_progressif(base_imposable_totale, bareme_succession)
    part_cto = 0.0 if actif_total_cto == 0 else capital_final_cto / actif_total_cto
    droits_cto = droits_totaux_cto * part_cto
    droits_autres_cto = droits_totaux_cto - droits_cto
    heritage_autres_cto = inputs.autres_biens_valeur - droits_autres_cto
    heritage_total_cto = heritage_cto + heritage_autres_cto

    base_totale = actif_total_cto
    difference_totale = heritage_total_av - heritage_total_cto
    relative_difference = None
    if base_totale > 0:
        relative_difference = difference_totale / base_totale

    details = {
        "abattement_succession_unitaire": abattement_par_heritier,
        "abattement_succession_total": abattement_succession_total,
        "abattement_av_unitaire": abattement_av,
        "abattement_av_total": abattement_fiscal_av_total,
        "droits_autres_biens_scenario_av": droits_autres_biens_av,
        "droits_totaux_scenario_cto": droits_totaux_cto,
        "droits_cto": droits_cto,
        "droits_autres_biens_scenario_cto": droits_autres_cto,
    }

    result = ComparisonResult(
        heritage_av=heritage_av,
        heritage_cto=heritage_cto,
        heritage_autres_av=heritage_autres_av,
        heritage_autres_cto=heritage_autres_cto,
        heritage_total_av=heritage_total_av,
        heritage_total_cto=heritage_total_cto,
        capital_final_av=capital_final_av,
        capital_final_cto=capital_final_cto,
        patrimoine_total_av=patrimoine_total_av,
        patrimoine_total_cto=actif_total_cto,
        part_taxable_av=base_autres_biens_av,
        part_taxable_cto=base_imposable_totale,
        impots_payes_av=droits_autres_biens_av,
        impots_payes_cto=droits_totaux_cto,
        difference_totale=difference_totale,
        relative_difference=relative_difference,
        base_totale=base_totale,
    )
    return result, details

@app.route("/", methods=["GET", "POST"])
def index():
    default_values = {
        "capital_initial": "100000",
        "autres_biens_valeur": "300000",
        "duree": "20",
        "rendement_annuel": "0.04",
        "frais_gestion_av": "0.0075",
        "frais_sociaux_av": "0.172",
        "nb_heriters": "1",
        "nb_beneficiaires": "1",
        "lien": "ligne_directe",
        "versements_av_avant70": "on",
    }

    errors = []
    result = None
    details = None

    if request.method == "POST":
        try:
            inputs = ScenarioInputs(
                capital_initial=float(request.form.get("capital_initial", default_values["capital_initial"])),
                autres_biens_valeur=float(request.form.get("autres_biens_valeur", default_values["autres_biens_valeur"])),
                duree=float(request.form.get("duree", default_values["duree"])),
                rendement_annuel=float(request.form.get("rendement_annuel", default_values["rendement_annuel"])),
                frais_gestion_av=float(request.form.get("frais_gestion_av", default_values["frais_gestion_av"])),
                frais_sociaux_av=float(request.form.get("frais_sociaux_av", default_values["frais_sociaux_av"])),
                nb_heriters=int(request.form.get("nb_heriters", default_values["nb_heriters"])),
                nb_beneficiaires=int(request.form.get("nb_beneficiaires", default_values["nb_beneficiaires"])),
                lien=request.form.get("lien", default_values["lien"]),
                versements_av_avant70=request.form.get("versements_av_avant70") is not None,
            )
            if inputs.nb_heriters <= 0:
                raise ValueError("Le nombre d'héritiers doit être strictement positif.")
            if inputs.nb_beneficiaires <= 0:
                raise ValueError("Le nombre de bénéficiaires doit être strictement positif.")
            if inputs.duree < 0:
                raise ValueError("La durée doit être positive.")
            result, details = compute_comparison(inputs)
        except ValueError as exc:
            errors.append(str(exc))

    return render_template(
        "index.html",
        defaults=default_values,
        result=result,
        details=details,
        errors=errors,
        form_values=request.form if request.method == "POST" else default_values,
    )


if __name__ == "__main__":
    app.run(debug=True)
