
from CTO_vs_AV import (
    calculer_heritage_assurance_vie,
    calculer_heritage_cto,
    get_regime_successoral,
    AssuranceVieResult
)
import numpy as np

def verify_reddit_scenario_1():
    print("--- Verification Reddit Scenario 1 (Profil Prudent) ---")
    # Données Reddit
    # Capital initial: 100,000€
    # Autres biens: 300,000€
    # Rendement: 5.0% par an
    # Durée: 15 ans
    # Bénéficiaires: 2
    # Frais AV: 0.5% (hypothèse commentateur) -> On suppose frais gestion. Pas de frais entrée/versement mentionnés.
    # On suppose versements AVANT 70 ans standard.
    
    capital = 100_000
    autres_biens = 300_000
    rendement = 0.05
    duree = 15
    nb_beneficiaires = 2
    frais_av = 0.005
    frais_sociaux = 0.172 # Standard
    
    # --- Calcul AV ---
    # Hypothèse: Abattement 152 500 par bénéficiaire
    abattement_av = 152_500 * nb_beneficiaires
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    
    res_av = calculer_heritage_assurance_vie(
        capital, duree, rendement, frais_av, frais_sociaux,
        abattement_av, bareme_av
    )
    
    print(f"AV - Valeur Brute (Capital Final): {res_av.capital_final}")
    print(f"AV - Plus-Values: {res_av.capital_final - capital}")
    print(f"AV - Droits Succession (Taxe AV): {res_av.droits_av}")
    print(f"AV - Valeur Nette Transmise: {res_av.heritage_net}")
    
    # --- Calcul CTO ---
    regime = "ligne_directe" # Hypothèse 2 enfants
    abattement_par_heritier, bareme_succession = get_regime_successoral(regime)
    abattement_succession_total = abattement_par_heritier * nb_beneficiaires # 2 héritiers
    
    res_cto = calculer_heritage_cto(
        capital, duree, rendement,
        autres_biens, abattement_succession_total, bareme_succession
    )
    
    print(f"CTO - Valeur Brute: {res_cto.capital_final}")
    print(f"CTO - Plus-Values: {res_cto.capital_final - capital}")
    print(f"CTO - Droits Succession (Part CTO): {res_cto.droits_imputes_cto}")
    print(f"CTO - Valeur Nette Transmise: {res_cto.heritage_net}")

    print("\n--- Comparaison ---")
    diff = res_av.heritage_net - res_cto.heritage_net
    print(f"Différence (AV - CTO): {diff}")
    
if __name__ == "__main__":
    verify_reddit_scenario_1()
