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
    impots_support_av: float
    impots_autres_av: float
    impots_support_cto: float
    impots_autres_cto: float
    prelevements_sociaux_av: float
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
        # Régime 757 B : 30 500 € pour l'ensemble des bénéficiaires
        abattement_av = 30_500 / max(1, inputs.nb_beneficiaires)
        bareme_av = [(float("inf"), 0.0)]

    abattement_fiscal_av_total = abattement_av * inputs.nb_beneficiaires

    av_result = calculer_heritage_assurance_vie(
        inputs.capital_initial,
        inputs.duree,
        inputs.rendement_annuel,
        inputs.frais_gestion_av,
        inputs.frais_sociaux_av,
        abattement_fiscal_av_total,
        abattement_fiscal_av_total,
        bareme_av,
        versement_apres_70=(not inputs.versements_av_avant70)
    )
    heritage_av = av_result.heritage_net
    capital_final_av = av_result.capital_final
    prelevements_sociaux_av = av_result.prelevements_sociaux
    droits_av = av_result.droits_av

    # Calcul des droits sur "Autres Biens + Part Taxable AV (757B)"
    base_taxable_av_scenario = inputs.autres_biens_valeur + getattr(av_result, 'montant_soumis_succession', 0.0)
    base_imposable_av_scenario = max(0.0, base_taxable_av_scenario - abattement_succession_total)
    
    droits_succession_scenario_av = calcul_impot_progressif(base_imposable_av_scenario, bareme_succession)
    
    # Répartition des droits (optionnel, pour l'affichage) :
    # On peut considérer que les droits sur "autres biens" sont la part proratisée, ou le marginal.
    # Ici, simplifions : heritage_autres_av = Autres_Biens - (Droits_Totaux - Part_Du_Au_AV)
    # Ou plus simple : Heritage_Total = (Net_AV + Autres_Biens) - Droits_Totaux_Scenario
    
    # Pour garder la structure actuelle :
    heritage_total_av = (heritage_av + inputs.autres_biens_valeur) - droits_succession_scenario_av
    
    # On déduit les droits "attribués" aux autres biens par différence avec le net AV (qui est déjà net de droits AV spécifiques mais brut de droits succession 757B)
    # Attention: heritage_av calculé par la fonction est net de 990I, mais brut de 757B.
    # Donc heritage_av (poche AV) doit payer sa part de droits succ.
    
    # Approche plus robuste :
    # Droits Totaux Scenario AV = droits_succession_scenario_av + droits_av (990I)
    impots_total_av = droits_succession_scenario_av + droits_av + prelevements_sociaux_av
    
    # On recalcule heritage_autres_av comme le reliquat pour que l'addition retombe juste ?
    # Non, restons cohérents avec ComparisonResult.
    
    # Disons que :
    # heritage_autres_av = valeur_autres - part_droits_autres
    # heritage_av_final = heritage_av_intermediaire - part_droits_av_757b
    
    # Pour faire simple et juste :
    patrimoine_total_av_brut = capital_final_av + inputs.autres_biens_valeur
    
    # Droits supportés par la part AV dans la succession (règle de trois sur l'assiette taxable ?)
    part_av_dans_assiette = 0.0
    if base_imposable_av_scenario > 0:
        part_av_dans_assiette = getattr(av_result, 'montant_soumis_succession', 0.0) / base_taxable_av_scenario
        
    droits_imputes_av_757b = droits_succession_scenario_av * part_av_dans_assiette
    droits_imputes_autres = droits_succession_scenario_av - droits_imputes_av_757b
    
    heritage_av_net_net = heritage_av - droits_imputes_av_757b
    heritage_autres_av = inputs.autres_biens_valeur - droits_imputes_autres
    
    # Override de heritage_av pour le résultat final
    heritage_av = heritage_av_net_net

    heritage_total_av = heritage_av + heritage_autres_av
    patrimoine_total_av = capital_final_av + inputs.autres_biens_valeur

    cto_result = calculer_heritage_cto(
        inputs.capital_initial,
        inputs.duree,
        inputs.rendement_annuel,
        inputs.autres_biens_valeur,
        abattement_succession_total,
        bareme_succession,
    )
    heritage_cto = cto_result.heritage_net
    capital_final_cto = cto_result.capital_final
    droits_cto = cto_result.droits_imputes_cto
    droits_totaux_cto = cto_result.droits_totaux

    actif_total_cto = capital_final_cto + inputs.autres_biens_valeur
    base_imposable_totale = max(0.0, actif_total_cto - abattement_succession_total)
    droits_autres_cto = droits_totaux_cto - droits_cto
    heritage_autres_cto = inputs.autres_biens_valeur - droits_autres_cto
    heritage_total_cto = heritage_cto + heritage_autres_cto

    impots_support_av = prelevements_sociaux_av + droits_av + droits_imputes_av_757b
    impots_autres_av = droits_imputes_autres
    impots_support_cto = droits_cto
    impots_autres_cto = droits_autres_cto
    impots_total_av = impots_support_av + impots_autres_av
    impots_total_cto = droits_totaux_cto

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
        "prelevements_sociaux_av": prelevements_sociaux_av,
        "droits_sur_assurance_vie": droits_av + droits_imputes_av_757b,
        "droits_autres_biens_scenario_av": droits_imputes_autres,
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
        part_taxable_av=base_imposable_av_scenario,
        part_taxable_cto=base_imposable_totale,
        impots_payes_av=impots_total_av,  # PS inclus ? Non, impots_total_av defini plus haut comme: droits_scenario + droits_av (990I) + PS?
        # Check definition ligne 116: impots_total_av = impots_support_av + impots_autres_av 
        # Et impots_support_av contient PS + droits. Donc OK.
        impots_payes_cto=impots_total_cto,
        impots_support_av=impots_support_av,
        impots_autres_av=impots_autres_av,
        impots_support_cto=impots_support_cto,
        impots_autres_cto=impots_autres_cto,
        prelevements_sociaux_av=prelevements_sociaux_av,
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
