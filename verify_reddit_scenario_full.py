
from CTO_vs_AV import (
    calculer_heritage_assurance_vie,
    calculer_heritage_cto,
    get_regime_successoral,
    AssuranceVieResult
)
import numpy as np

def run_simulation(name, capital, autres_biens, rendement, duree, nb_beneficiaires, frais_av, expected_av_net, expected_cto_net):
    print(f"\n=== {name} ===")
    frais_sociaux = 0.172
    
    # --- AV ---
    abattement_av = 152_500 * nb_beneficiaires
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    res_av = calculer_heritage_assurance_vie(
        capital, duree, rendement, frais_av, frais_sociaux,
        abattement_av, bareme_av
    )
    
    # --- CTO ---
    regime = "ligne_directe"
    abattement_par_heritier, bareme_succession = get_regime_successoral(regime)
    abattement_succession_total = abattement_par_heritier * nb_beneficiaires
    res_cto = calculer_heritage_cto(
        capital, duree, rendement,
        autres_biens, abattement_succession_total, bareme_succession
    )
    
    # --- Comparison ---
    print(f"AV Code: {res_av.heritage_net:,.0f} | Reddit: {expected_av_net:,.0f} | Delta: {res_av.heritage_net - expected_av_net:,.0f}")
    print(f"CTO Code: {res_cto.heritage_net:,.0f} | Reddit: {expected_cto_net:,.0f} | Delta: {res_cto.heritage_net - expected_cto_net:,.0f}")
    
    winner_code = "CTO" if res_cto.heritage_net > res_av.heritage_net else "AV"
    input_winner = "CTO" if expected_cto_net > expected_av_net else "AV"
    print(f"Winner Code: {winner_code} | Winner Reddit: {input_winner}")

def verify_all_scenarios():
    # Scenario 1
    run_simulation(
        name="Scenario 1 (Prudent, 100k)",
        capital=100_000, autres_biens=300_000, rendement=0.05, duree=15, 
        nb_beneficiaires=2, frais_av=0.005,
        expected_av_net=177441, expected_cto_net=184165
    )
    
    # Scenario 2
    run_simulation(
        name="Scenario 2 (100% Actions, 500k, autres 300k)",
        capital=500_000, autres_biens=300_000, rendement=0.095, duree=15, 
        nb_beneficiaires=2, frais_av=0.005,
        expected_av_net=1243350, expected_cto_net=1495102
    )
    
    # Scenario 3
    run_simulation(
        name="Scenario 3 (RP 600k, 500k investis)",
        capital=500_000, autres_biens=600_000, rendement=0.095, duree=15, 
        nb_beneficiaires=2, frais_av=0.005,
        expected_av_net=1243350, expected_cto_net=1456912
    )

    # Scenario 4 (Fat FIRE)
    run_simulation(
        name="Scenario 4 (Fat FIRE 5M)",
        capital=5_000_000, autres_biens=1_000_000, rendement=0.095, duree=15, 
        nb_beneficiaires=2, frais_av=0.005,
        expected_av_net=10466999, expected_cto_net=11266284
    )

if __name__ == "__main__":
    verify_all_scenarios()
