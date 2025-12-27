
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
    if vmin < 0 and vmax > 0:
        norm = TwoSlopeNorm(vmin=min(vmin, -1), vcenter=0, vmax=max(vmax, 1))
    else:
        norm = Normalize(vmin=vmin, vmax=vmax)
    
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
    print("Generating High Wealth Heatmap...")
    resol = 200
    
    # Simulation Params: "High Wealth / Titanium"
    # We look for the "Tax Shield" effect of AV (31.25% vs 45%)
    
    # Range: Capital 1M -> 15M / Duration 10 -> 50y
    capitals = np.linspace(1_000_000, 15_000_000, resol)
    durations = np.linspace(10, 50, resol)
    
    # Fixed Params
    rendement = 0.08 # 8% (Actions Monde)
    frais_av = 0.006 # 0.6% excelent contrat
    frais_sociaux = 0.172
    nb_benef = 2 # Famille
    
    abattement_av_total = 152_500 * nb_benef
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    
    abattement_par_heritier, bareme_succ = get_regime_successoral("ligne_directe")
    abattement_succ_total = abattement_par_heritier * nb_benef
    autres_biens = 1_000_000 # Déjà un patrimoine immo conséquent, donc tranches basses mangées
    
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
                
    plot_heatmap(Z, durations, capitals/1_000_000, 
                 "Durée (Années)", "Capital Initial (Millions €)", 
                 "Gros Patrimoine (8%/an, Frais 0.6%, Autres Biens 1M€)", 
                 "heatmap_high_wealth.png")

if __name__ == "__main__":
    run()
