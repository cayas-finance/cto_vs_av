
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from CTO_vs_AV import (
    calculer_heritage_assurance_vie,
    calculer_heritage_cto,
    get_regime_successoral
)

def run():
    print("Generating Sibling Transmission Heatmap (5% Yield)...")
    resol = 200
    
    # Ranges
    capitals = np.geomspace(100_000, 15_000_000, resol)
    durations = np.linspace(10, 60, resol)
    
    # Fixed Params
    rendement = 0.05 
    frais_av = 0.005 # 0.5% (Correcting user's 9.5% assumption)
    frais_sociaux = 0.172
    nb_benef = 1 # Simulation for 1 brother/sister
    
    # AV specific for siblings: Same 990 I rule (152.5k abatement then 20%/31.25%)
    # This is the HUGE advantage vs 35%/45% inheritance tax
    abattement_av_total = 152_500 * nb_benef
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    
    # CTO specific for siblings
    abattement_par_heritier, bareme_succ = get_regime_successoral("frere_soeur")
    abattement_succ_total = abattement_par_heritier * nb_benef
    # Assumption: No other goods consumed the abatement? Or maybe they did?
    # Abatement is small (15k), so it doesn't matter much. Let's say 0 other goods to be clean.
    autres_biens = 0 
    
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
    # Expecting mostly GREEN (Positive) here due to 45% tax vs 20/31%
    div_norm_min = min(vmin, -2.0) 
    div_norm_max = max(vmax, 2.0)
    norm = TwoSlopeNorm(vmin=div_norm_min, vcenter=0, vmax=div_norm_max)
    
    plt.pcolormesh(durations, capitals/1_000_000, Z, cmap='RdYlGn', norm=norm, shading='auto')
    plt.colorbar(label="Avantage Net Relatif (%) : Vert = AV, Rouge = CTO")
    
    plt.yscale('log')
    plt.yticks([0.1, 0.2, 0.5, 1, 2, 5, 10, 15], ["0.1M", "0.2M", "0.5M", "1M", "2M", "5M", "10M", "15M"])
    
    plt.xlabel("Durée de détention (Années)")
    plt.ylabel("Capital Initial (Millions €) - Échelle Log")
    plt.title(f"Frère/Soeur : AV vs CTO (5%/an, Frais 0.5%)")
    
    plt.contour(durations, capitals/1_000_000, Z, levels=[0], colors='black', linestyles='dashed')

    filename = "heatmap_siblings_5pct.png"
    plt.savefig(filename)
    print(f"Saved {filename}")

if __name__ == "__main__":
    run()
