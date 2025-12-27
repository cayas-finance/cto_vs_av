
import numpy as np
from CTO_vs_AV import calculer_heritage_assurance_vie, calculer_heritage_cto, get_regime_successoral

def scan_victory_zone(yield_val):
    print(f"\n=== SCANNING VICTORY ZONE: Yield {yield_val*100}% ===")
    
    capitals = [100_000, 300_000, 500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000]
    durations = [10, 15, 20, 25, 30, 40, 50]
    
    fee_av = 0.005
    frais_sociaux = 0.172
    abattement_av_total = 152_500 * 2 # 2 benefs used in heatmaps
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    
    autres_biens = 1_000_000 # As per heatmap assumption
    abattement_par_heritier, bareme_succ = get_regime_successoral("ligne_directe")
    abattement_succ_total = abattement_par_heritier * 2
    
    winners = []
    
    for cap in capitals:
        row = []
        for dur in durations:
            av = calculer_heritage_assurance_vie(cap, dur, yield_val, fee_av, frais_sociaux, abattement_av_total, bareme_av).heritage_net
            cto = calculer_heritage_cto(cap, dur, yield_val, autres_biens, abattement_succ_total, bareme_succ).heritage_net
            
            diff = av - cto
            if diff > 0:
                row.append("AV")
            else:
                row.append("CTO")
        winners.append((cap, row))
        
    # Print grid
    print(f"       Durations: {durations}")
    for cap, row in winners:
        print(f"Cap {cap:10,.0f}: {row}")

def scan_victory_zone_sibling(yield_val):
    print(f"\n=== SCANNING VICTORY ZONE SIBLING: Yield {yield_val*100}% ===")
    
    capitals = [100_000, 300_000, 500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000, 15_000_000]
    durations = [10, 20, 25, 30, 35, 40, 50, 60]
    
    fee_av = 0.005
    frais_sociaux = 0.172
    abattement_av_total = 152_500 # 1 benef
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    
    # Sibling params
    autres_biens = 0
    abattement_par_heritier, bareme_succ = get_regime_successoral("frere_soeur")
    abattement_succ_total = abattement_par_heritier # 1 heir
    
    winners = []
    
    for cap in capitals:
        row = []
        for dur in durations:
            av = calculer_heritage_assurance_vie(cap, dur, yield_val, fee_av, frais_sociaux, abattement_av_total, bareme_av).heritage_net
            cto = calculer_heritage_cto(cap, dur, yield_val, autres_biens, abattement_succ_total, bareme_succ).heritage_net
            
            diff = av - cto
            if diff > 0:
                row.append("AV")
            else:
                row.append("CTO")
        winners.append((cap, row))
        
    # Print grid
    print(f"       Durations: {durations}")
    for cap, row in winners:
        print(f"Cap {cap:10,.0f}: {row}")

def run():
    # scan_victory_zone(0.03)
    # scan_victory_zone(0.05)
    # scan_victory_zone(0.08)
    scan_victory_zone_sibling(0.05)

if __name__ == "__main__":
    run()
