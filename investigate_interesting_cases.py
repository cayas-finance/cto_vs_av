
import numpy as np
from CTO_vs_AV import calculer_heritage_assurance_vie, calculer_heritage_cto, get_regime_successoral

def investigate():
    print("=== INVESTIGATION CAS INTERESSANTS ===\n")
    
    # Common params
    duration = 20
    nb_heirs = 1
    social_fees = 0.172
    abattement_succ = 100_000 # Ligne directe
    
    # CAS A: IMPACT DES FRAIS (Break-even fee)
    # 100k, 20 ans, 5% yield. Fees 0.0% -> 2.0%
    print("--- A. Impact des Frais (100k, 20 ans, 5%) ---")
    capital = 100_000
    autres_biens = 300_000 # Abatement consumed
    yield_val = 0.05
    
    base_cto = calculer_heritage_cto(capital, duration, yield_val, autres_biens, abattement_succ, [(8072, 0.05), (12109, 0.1), (15932, 0.15), (552324, 0.2), (np.inf, 0.3)])
    # Note: manually passing simplified brackets or calling get_regime
    ab_h, bareme_succ = get_regime_successoral("ligne_directe")
    
    res_cto = calculer_heritage_cto(capital, duration, yield_val, autres_biens, ab_h, bareme_succ).heritage_net

    print(f"Net CTO (Ref): {res_cto:,.0f} €")
    
    for fee in [0.003, 0.005, 0.006, 0.008, 0.010, 0.015]:
        res_av = calculer_heritage_assurance_vie(
            capital, duration, yield_val, fee, social_fees, 152_500, [(700_000, 0.2), (np.inf, 0.3125)]
        ).heritage_net
        diff = res_av - res_cto
        print(f"Frais AV {fee*100:4.1f}% -> Net AV: {res_av:,.0f} € | Diff: {diff:+,.0f} €")

    # CAS B: LE PETIT PORTEUR (Small Wealth)
    # 50k, 20 ans, 5%. 0 Autres biens.
    # Abattement succession NON consommé.
    print("\n--- B. Le Petit Porteur (50k, 0 autres biens) ---")
    capital = 50_000
    autres_biens = 0
    yield_val = 0.05
    fees = 0.006
    
    res_cto_small = calculer_heritage_cto(capital, duration, yield_val, autres_biens, ab_h, bareme_succ).heritage_net
    res_av_small = calculer_heritage_assurance_vie(
        capital, duration, yield_val, fees, social_fees, 152_500, [(700_000, 0.2), (np.inf, 0.3125)]
    ).heritage_net
    
    print(f"Net CTO: {res_cto_small:,.0f} € (Taxe: {calculer_heritage_cto(capital, duration, yield_val, autres_biens, ab_h, bareme_succ).droits_imputes_cto:.0f})")
    print(f"Net AV : {res_av_small:,.0f} € (Frais 0.6%)")
    print(f"Winner: {'CTO' if res_cto_small > res_av_small else 'AV'} by {abs(res_cto_small - res_av_small):.0f} €")

    # CAS C: PERFORMANCE (High Yield)
    # 100k, 20 ans, Fees 0.6%. Yield 2% vs 10%
    print("\n--- C. Impact Performance (2% vs 10%) ---")
    capital = 100_000
    autres_biens = 300_000
    fees = 0.006
    
    for y in [0.02, 0.10]:
        r_cto = calculer_heritage_cto(capital, duration, y, autres_biens, ab_h, bareme_succ).heritage_net
        r_av = calculer_heritage_assurance_vie(capital, duration, y, fees, social_fees, 152_500, [(700_000, 0.2), (np.inf, 0.3125)]).heritage_net
        print(f"Yield {y*100:.0f}% -> CTO: {r_cto:,.0f} | AV: {r_av:,.0f} | Diff: {r_av - r_cto:+,.0f}")

if __name__ == "__main__":
    investigate()
