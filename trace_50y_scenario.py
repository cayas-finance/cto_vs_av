
import numpy as np
from CTO_vs_AV import calculer_heritage_assurance_vie, calculer_heritage_cto, get_regime_successoral

def trace_50y(yield_val):
    capital = 5_000_000 # 5M
    duration = 50
    fee_av = 0.005 # 0.5%
    frais_sociaux = 0.172
    
    # AV Params
    abattement_av_total = 152_500 * 2 # 2 benefs
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    
    # CTO Params
    autres_biens = 1_000_000
    abattement_par_heritier, bareme_succ = get_regime_successoral("ligne_directe")
    abattement_succ_total = abattement_par_heritier * 2
    
    print(f"\n--- Scenario: 5M€, 50 years, Yield {yield_val*100}% ---")
    
    # CTO
    cto_res = calculer_heritage_cto(capital, duration, yield_val, autres_biens, abattement_succ_total, bareme_succ)
    print(f"CTO Net: {cto_res.heritage_net:,.0f} €")
    
    # AV
    av_res = calculer_heritage_assurance_vie(capital, duration, yield_val, fee_av, frais_sociaux, abattement_av_total, bareme_av)
    print(f"AV Net : {av_res.heritage_net:,.0f} €")
    print(f"AV Details -> Final: {av_res.capital_final:,.0f} | PS: {av_res.prelevements_sociaux:,.0f} | Tax: {av_res.droits_av:,.0f}")
    
    diff = av_res.heritage_net - cto_res.heritage_net
    print(f"Result: {'AV' if diff > 0 else 'CTO'} wins by {diff:+,.0f} €")

def run():
    trace_50y(0.02)
    trace_50y(0.05)
    trace_50y(0.08)
    trace_50y(0.10)
    trace_50y(0.15)

if __name__ == "__main__":
    run()
