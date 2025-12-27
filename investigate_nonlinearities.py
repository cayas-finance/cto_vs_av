
import numpy as np
from CTO_vs_AV import calculer_heritage_assurance_vie, calculer_heritage_cto, get_regime_successoral

def trace_scenario(name, duration, yield_val):
    print(f"\n=== TRACE SCENARIO: {name} ===")
    print(f"Params: Duration={duration} years, Yield={yield_val*100}%")
    
    # Params from specific_heatmaps.py (Heatmap 2)
    capital = 100_000
    fee_av = 0.006
    frais_sociaux = 0.172
    abattement_av_total = 152_500
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    
    autres_biens = 300_000
    abattement_par_heritier, bareme_succ = get_regime_successoral("ligne_directe")
    abattement_succ_total = abattement_par_heritier # 1 benef
    
    # 1. Calcul CTO
    # Note: calculated directly to see details inside if we could, but here we inspect output
    cto_res = calculer_heritage_cto(capital, duration, yield_val, autres_biens, abattement_succ_total, bareme_succ)
    
    print(f"\n--- CTO ---")
    print(f"Capital Final Brut: {cto_res.capital_final:,.0f} €")
    print(f"  (Gain Latent Purged: {cto_res.capital_final - capital:,.0f} €)")
    print(f"Patrimoine Total Succession (avec 300k autres): {cto_res.capital_final + autres_biens:,.0f} €")
    print(f"Droits Succession Totaux: {cto_res.droits_totaux:,.0f} €")
    print(f"Droits Imputés CTO: {cto_res.droits_imputes_cto:,.0f} €")
    print(f"NET CTO: {cto_res.heritage_net:,.0f} €")
    
    # 2. Calcul AV
    av_res = calculer_heritage_assurance_vie(capital, duration, yield_val, fee_av, frais_sociaux, abattement_av_total, bareme_av)
    
    print(f"\n--- AV ---")
    print(f"Capital Final Brut (avant PS): {av_res.capital_final:,.0f} €")
    print(f"  (Frais Gestion impact estimated: ca. {(capital*(1+yield_val)**duration) - av_res.capital_final:,.0f} € lost to fees vs CTO gross)")
    print(f"Prélèvements Sociaux (17.2% sur gains): -{av_res.prelevements_sociaux:,.0f} €")
    print(f"Capital Net PS: {av_res.capital_final - av_res.prelevements_sociaux:,.0f} €")
    print(f"  (Assiette Taxable AV: {max(0, av_res.capital_final - av_res.prelevements_sociaux - abattement_av_total):,.0f} €)")
    print(f"Droits Succession AV (20%/31.25%): -{av_res.droits_av:,.0f} €")
    print(f"NET AV: {av_res.heritage_net:,.0f} €")
    
    # 3. Comparison
    diff = av_res.heritage_net - cto_res.heritage_net
    pct = (diff / cto_res.heritage_net) * 100
    print(f"\n>>> RESULT: Diff = {diff:+,.0f} € | Relatif = {pct:+.2f} %")

def run():
    # Case A: 30 years, 7% yield -> User says ~ -20%
    trace_scenario("Cas A (Moyen)", 30, 0.07)
    
    # Case B: 30 years, 10% yield -> User says ~ -5% (My calc says -18%)
    trace_scenario("Cas B (Gros Rendement)", 30, 0.10)
    
    # Case C: 40 years, 10% yield -> Limits of compounding
    trace_scenario("Cas C (40 ans, 10%)", 40, 0.10)

if __name__ == "__main__":
    run()
