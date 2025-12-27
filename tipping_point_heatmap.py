
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from CTO_vs_AV import (
    calculer_heritage_assurance_vie,
    calculer_heritage_cto,
    get_regime_successoral
)

def generate_heatmap(rendement):
    print(f"Generating Tipping Point Heatmap for {rendement*100}%...")
    resol = 200
    
    # Ranges
    # Capital: 100k -> 15M (Log scale)
    capitals = np.geomspace(100_000, 15_000_000, resol)
    # Duration: 10 -> 60 years
    durations = np.linspace(10, 60, resol)
    
    # Fixed Params
    frais_av = 0.005 
    frais_sociaux = 0.172
    nb_benef = 2 
    
    abattement_av_total = 152_500 * nb_benef
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    
    abattement_par_heritier, bareme_succ = get_regime_successoral("ligne_directe")
    abattement_succ_total = abattement_par_heritier * nb_benef
    autres_biens = 1_000_000 
    
    Z = np.zeros((resol, resol))
    
    for i, cap in enumerate(capitals): # Y axis
        for j, dur in enumerate(durations): # X axis
            av = calculer_heritage_assurance_vie(
                cap, dur, rendement, frais_av, frais_sociaux, 
                abattement_av_total, bareme_av
            ).heritage_net
            
            cto = calculer_heritage_cto(
                cap, dur, rendement, autres_biens, 
                abattement_succ_total, bareme_succ
            ).heritage_net
            
            if cto > 0:
                Z[i, j] = (av - cto) / cto * 100.0
            else:
                Z[i, j] = 0.0
    
    plt.figure(figsize=(12, 10))
    vmin = np.min(Z)
    vmax = np.max(Z)
    
    # Center on 0
    div_norm_min = min(vmin, -2.0)
    div_norm_max = max(vmax, 2.0)
    norm = TwoSlopeNorm(vmin=div_norm_min, vcenter=0, vmax=div_norm_max)
    
    plt.pcolormesh(durations, capitals/1_000_000, Z, cmap='RdYlGn', norm=norm, shading='auto')
    plt.colorbar(label="Avantage Net Relatif (%) : Vert = AV, Rouge = CTO")
    
    plt.yscale('log')
    plt.yticks([0.1, 0.2, 0.5, 1, 2, 5, 10, 15], ["0.1M", "0.2M", "0.5M", "1M", "2M", "5M", "10M", "15M"])
    
    plt.xlabel("Durée de détention (Années)")
    plt.ylabel("Capital Initial (Millions €) - Échelle Log")
    plt.title(f"Point de Bascule AV vs CTO ({rendement*100:.0f}%/an, Frais 0.5%)")
    
    plt.contour(durations, capitals/1_000_000, Z, levels=[0], colors='black', linestyles='dashed')

    filename = f"heatmap_tipping_point_{int(rendement*100)}pct.png"
    plt.savefig(filename)
    print(f"Saved {filename}")
    plt.close()

def run():
    generate_heatmap(0.03)
    generate_heatmap(0.05)
    # generate_heatmap(0.08) # Already done, but can re-run if needed. User asked for "other graph", implies addition.

if __name__ == "__main__":
    run()
