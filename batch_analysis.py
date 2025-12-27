
import csv
import itertools
from dataclasses import dataclass, asdict
from typing import List, Dict
import numpy as np

# Import core calculation logic
from CTO_vs_AV import (
    calculer_heritage_assurance_vie,
    calculer_heritage_cto,
    get_regime_successoral,
    AssuranceVieResult,
    CTOResult
)

@dataclass
class ScenarioInput:
    name: str  # e.g. "Profil Standard"
    capital_initial: float
    autres_biens: float
    duree: int
    rendement: float
    frais_av_gestion: float
    nb_beneficiaires: int
    versement_apres_70: bool
    lien_parente: str = "ligne_directe"

@dataclass
class ScenarioResult:
    input: ScenarioInput
    av_net: float
    cto_net: float
    diff_amount: float
    diff_percent: float
    winner: str
    av_tax_details: str
    cto_tax_details: str

def run_scenario(inp: ScenarioInput) -> ScenarioResult:
    # 1. AV Simulation
    frais_sociaux = 0.172
    
    # Setup Abattement AV logic based on age
    if inp.versement_apres_70:
        # 757 B
        abattement_av_global = 30_500
        # Répartition : ici on simplifie, on considère que ce contrat utilise sa part d'abattement
        # Si on a N bénéficiaires, on divise l'abattement global par N pour ce calcul unitaire
        abattement_contrat = abattement_av_global / max(1, inp.nb_beneficiaires)
        bareme_av = [(np.inf, 0.0)] # Pas de 990 I
    else:
        # 990 I (< 70 ans)
        abattement_contrat = 152_500 * inp.nb_beneficiaires # Total pour ce contrat si N bénéficiaires nommés
        bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]

    av_res = calculer_heritage_assurance_vie(
        inp.capital_initial, 
        inp.duree, 
        inp.rendement, 
        inp.frais_av_gestion, 
        frais_sociaux,
        abattement_contrat,
        bareme_av,
        versement_apres_70=inp.versement_apres_70
    )

    # Réintégration Fiscale AV (pour successions 757B et autres biens marginaux)
    # L'AV > 70 ans génère des droits de succession classiques sur (Primes - 30.5k).
    # Ils s'ajoutent aux "autres biens".
    # Calculons l'impact marginal.
    
    abattement_par_heritier, bareme_succ = get_regime_successoral(inp.lien_parente)
    abattement_succ_total = abattement_par_heritier * inp.nb_beneficiaires
    
    # NOTE: Dans cette simulation batch, on cherche à comparer "à partir de rien" ou "en marginal" ?
    # Le paramètre "autres_biens" sert à positionner la tranche marginale.
    
    # -- Côté AV --
    # On calcule l'impôt TOTAL (Autres biens + AV > 70ans potentielle)
    base_autres = max(0, inp.autres_biens - abattement_succ_total)
    droits_sur_autres_seuls = 0.0 # On ne les compte pas dans le coût AV, on regarde le delta
    
    # Quelle est la valeur nette AV ? 
    # C'est (Valeur rachat nette PS - Droits 990I) - (Part droits succession générée par l'AV)
    
    # Calcul droits succession générés par AV 757B
    montant_757b = av_res.montant_soumis_succession
    
    impot_marginal_av = 0.0
    if montant_757b > 0:
        # Droits avec AV
        base_avec_av = max(0, inp.autres_biens + montant_757b - abattement_succ_total)
        # Droits sans AV (juste les autres biens)
        base_sans_av = max(0, inp.autres_biens - abattement_succ_total)
        
        tax_avec = 0 # Need helper execution or re-impl
        # On va réutiliser les helpers de CTO_vs_AV si possible, ou appeler la fonction calcul_impot_progressif
        # Import local pour éviter souci scope si script lancé direct
        from CTO_vs_AV import calcul_impot_progressif
        
        droits_total = calcul_impot_progressif(base_avec_av, bareme_succ)
        droits_base = calcul_impot_progressif(base_sans_av, bareme_succ)
        
        impot_marginal_av = droits_total - droits_base
    
    av_net_pocket = av_res.heritage_net - impot_marginal_av

    # -- Côté CTO --
    cto_res = calculer_heritage_cto(
        inp.capital_initial, 
        inp.duree, 
        inp.rendement, 
        inp.autres_biens,
        abattement_succ_total,
        bareme_succ
    )
    # cto_res.heritage_net contient déjà la déduction de la part "imputée" au CTO dans les droits totaux.
    
    # Result
    diff = av_net_pocket - cto_res.heritage_net
    winner = "AV" if diff > 0 else "CTO"
    
    # Pourcentage relatif au capital final BRUT (pour donner une idée de la perte de valeur)
    # ou relatif au CTO net ?
    # Utilisons relatif au CTO Net par convention
    pct = 0.0
    if cto_res.heritage_net > 0:
        pct = (diff / cto_res.heritage_net) * 100
        
    return ScenarioResult(
        input=inp,
        av_net=av_net_pocket,
        cto_net=cto_res.heritage_net,
        diff_amount=diff,
        diff_percent=pct,
        winner=winner,
        av_tax_details=f"Droits 990I: {av_res.droits_av:.0f}, Droits 757B: {impot_marginal_av:.0f}",
        cto_tax_details=f"Droits Success: {cto_res.droits_imputes_cto:.0f} (Purge PV)"
    )

def generate_profiles():
    scenarios = []
    
    # 1. Jeune Actif (Début de construction)
    # Petit capital, horizon long, AV frais moyens vs CTO
    scenarios.append(ScenarioInput(
        "Jeune Actif (Start)", 10_000, 0, 30, 0.08, 0.006, 1, False
    ))
    
    # 2. Cadre Moyen (Patrimoine existant)
    # 100k à placer, déjà 300k immo, 2 enfants, 20 ans devant soi
    scenarios.append(ScenarioInput(
        "Cadre Standard", 100_000, 300_000, 20, 0.06, 0.006, 2, False
    ))
    
    # 3. Pré-Retraite (Gros placement)
    # 500k à placer, propriétaire (500k), 2 enfants, 15 ans (60->75 ans donc versement AVANT 70)
    scenarios.append(ScenarioInput(
        "Pré-Retraite (<70 ans)", 500_000, 500_000, 15, 0.05, 0.005, 2, False
    ))
    
    # 4. Senior (>70 ans, transmission court terme)
    # 100k, déjà bien doté (500k), 10 ans, versement APRES 70
    scenarios.append(ScenarioInput(
        "Senior (>70 ans)", 100_000, 500_000, 10, 0.04, 0.005, 2, True
    ))
    
    # 5. Very High Net Worth (Fat FIRE Reddit)
    # 5M€, 1M€ autres, 15 ans, rendements actions
    scenarios.append(ScenarioInput(
        "Fat FIRE (Reddit S4)", 5_000_000, 1_000_000, 15, 0.095, 0.005, 2, False
    ))
    
    # 6. Comparaison Frais AV (Impact 1% vs 0.5%)
    # Même profil Cadre Standard mais frais élevés
    scenarios.append(ScenarioInput(
        "Cadre (AV Banque Trad 1.5%)", 100_000, 300_000, 20, 0.06, 0.015, 2, False
    ))

    return scenarios

def run_batch():
    profs = generate_profiles()
    results = []
    
    print(f"{'PROFILE':<30} | {'WINNER':<5} | {'DIFF €':<12} | {'DIFF %':<8} | {'AV NET':<12} | {'CTO NET':<12}")
    print("-" * 100)
    
    for p in profs:
        res = run_scenario(p)
        results.append(res)
        print(f"{p.name:<30} | {res.winner:<5} | {res.diff_amount:+,.0f}".replace(",", " ") + f" € | {res.diff_percent:+.2f} % | {res.av_net:,.0f} | {res.cto_net:,.0f}")

    # Generate Markdown Report
    with open("analysis_report.md", "w") as f:
        f.write("# Rapport d'Analyse Comparative : AV vs CTO\n\n")
        f.write("Analyse basée sur les profils types définis.\n\n")
        f.write("| Profil | Vainqueur | Gain Net (€) | Gain Relatif (%) | Détails Fiscalité |\n")
        f.write("| :--- | :---: | ---: | ---: | :--- |\n")
        for r in results:
            clean_diff = f"{r.diff_amount:+,.0f}".replace(",", " ")
            details = f"AV: {r.av_tax_details}<br>CTO: {r.cto_tax_details}"
            f.write(f"| **{r.input.name}** | **{r.winner}** | {clean_diff} € | {r.diff_percent:+.2f}% | {details} |\n")
            
    # Generate CSV
    with open("batch_results.csv", "w", newline='') as csvfile:
        fieldnames = ['Profile', 'Capital', 'Other_Assets', 'Duration', 'Yield', 'Fees_AV', 'Age_Input', 'Winner', 'Diff_Euro', 'Diff_Pct', 'AV_Net', 'CTO_Net']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                'Profile': r.input.name,
                'Capital': r.input.capital_initial,
                'Other_Assets': r.input.autres_biens,
                'Duration': r.input.duree,
                'Yield': r.input.rendement,
                'Fees_AV': r.input.frais_av_gestion,
                'Age_Input': '>70' if r.input.versement_apres_70 else '<70',
                'Winner': r.winner,
                'Diff_Euro': r.diff_amount,
                'Diff_Pct': r.diff_percent,
                'AV_Net': r.av_net,
                'CTO_Net': r.cto_net
            })
            
    print("\nRapport généré : analysis_report.md")
    print("Données brutes : batch_results.csv")

if __name__ == "__main__":
    run_batch()
