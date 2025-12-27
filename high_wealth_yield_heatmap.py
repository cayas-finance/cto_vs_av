
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, Normalize
from CTO_vs_AV import (
    calculer_heritage_assurance_vie,
    calculer_heritage_cto,
    get_regime_successoral
)

def plot_heatmap(Z, x_range, y_range, x_label, y_label, title, filename):
    plt.figure(figsize=(12, 10))
    
    vmin = np.min(Z)
    vmax = np.max(Z)
    
    # Smart Normalization
    # Force centering on 0
    div_norm_min = min(vmin, -0.5)
    div_norm_max = max(vmax, 0.5)
    
    norm = TwoSlopeNorm(vmin=div_norm_min, vcenter=0, vmax=div_norm_max)
    
    plt.imshow(
        Z, 
        origin='lower', 
        extent=[x_range[0], x_range[-1], y_range[0], y_range[-1]], 
        aspect='auto',
        cmap='RdYlGn', 
        norm=norm
    )
    plt.colorbar(label="Avantage Net Relatif (%) : Vert = AV, Rouge = CTO")
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.savefig(filename)
    print(f"Saved {filename}")
    plt.close()

def run():
    print("Generating High Wealth Yield Heatmap...")
    resol = 200
    
    # Ranges
    # Capital: 1M -> 20M
    capitals = np.linspace(1_000_000, 20_000_000, resol)
    # Yield: 2% -> 15%
    yields = np.linspace(0.02, 0.15, resol)
    
    # Fixed Params
    duration = 50
    frais_av = 0.005 # 0.5% requested
    frais_sociaux = 0.172
    nb_benef = 2 
    
    abattement_av_total = 152_500 * nb_benef
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    
    abattement_par_heritier, bareme_succ = get_regime_successoral("ligne_directe")
    abattement_succ_total = abattement_par_heritier * nb_benef
    autres_biens = 1_000_000 
    
    Z = np.zeros((resol, resol))
    
    for i, cap in enumerate(capitals): # Y axis
        for j, yld in enumerate(yields): # X axis
            av = calculer_heritage_assurance_vie(
                cap, duration, yld, frais_av, frais_sociaux, 
                abattement_av_total, bareme_av
            ).heritage_net
            
            cto = calculer_heritage_cto(
                cap, duration, yld, autres_biens, 
                abattement_succ_total, bareme_succ
            ).heritage_net
            
            if cto > 0:
                Z[i, j] = (av - cto) / cto * 100.0
            else:
                Z[i, j] = 0.0
                
    plot_heatmap(Z, yields*100, capitals/1_000_000, 
                 "Rendement Annuel (%)", "Capital Initial (Millions €)", 
                 f"Gros Patrimoine (50 ans, Frais 0.5%, Autres Biens 1M€)", 
                 "heatmap_high_wealth_yield.png")

if __name__ == "__main__":
    run()
