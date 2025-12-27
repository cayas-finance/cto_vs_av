
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from CTO_vs_AV import (
    calculer_heritage_assurance_vie,
    calculer_heritage_cto,
    get_regime_successoral
)

def generate_capital_vs_duration_heatmap():
    print("Generating Heatmap: Capital vs Duration...")
    
    # Grid Parameters
    resol_x = 50 # Duration
    resol_y = 50 # Capital
    
    durations = np.linspace(1, 40, resol_x) # 1 to 40 years
    capitals = np.linspace(100_000, 6_000_000, resol_y) # 100k to 6M
    
    # Fixed Parameters
    autres_biens = 300_000
    nb_beneficiaires = 2
    rendement = 0.07 # 7% performance
    frais_av = 0.006 # 0.6% fees
    frais_sociaux = 0.172
    versement_apres_70 = False 
    
    # Output Grid
    Z = np.zeros((resol_y, resol_x))
    
    # Pre-calc Succession Parameters
    abattement_av_total = 152_500 * nb_beneficiaires
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    abattement_par_heritier, bareme_succession = get_regime_successoral("ligne_directe")
    abattement_succession_total = abattement_par_heritier * nb_beneficiaires
    
    for i, cap in enumerate(capitals):
        for j, dur in enumerate(durations):
            # AV Result
            av_res = calculer_heritage_assurance_vie(
                cap, dur, rendement, frais_av, frais_sociaux,
                abattement_av_total, bareme_av,
                versement_apres_70=versement_apres_70
            )
            # CTO Result
            cto_res = calculer_heritage_cto(
                cap, dur, rendement, autres_biens,
                abattement_succession_total, bareme_succession
            )
            
            # Difference (Positive = AV wins, Negative = CTO wins)
            diff = av_res.heritage_net - cto_res.heritage_net
            Z[i, j] = diff

    # Plotting
    plt.figure(figsize=(12, 8))
    
    # Normalize color map: 0 is white (neutral), Red is CTO, Blue/Green is AV
    vmin = np.min(Z)
    vmax = np.max(Z)
    norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
    
    plt.imshow(
        Z, 
        origin='lower', 
        extent=[durations[0], durations[-1], capitals[0]/1e6, capitals[-1]/1e6], 
        aspect='auto',
        cmap='RdYlGn', # Red = CTO (Negative), Green = AV (Positive)
        norm=norm
    )
    
    plt.colorbar(label="Avantage Net (€) : Vert = AV gagnante, Rouge = CTO gagnant")
    plt.xlabel("Durée de détention (Années)")
    plt.ylabel("Capital Initial (Millions €)")
    plt.title(f"Arbitrage AV vs CTO (Rendement 7%, Frais AV 0.6%, 2 héritiers)\nImpact Capital Initial vs Durée")
    
    # Save
    filename = "heatmap_capital_duration.png"
    plt.savefig(filename)
    print(f"Saved {filename}")

if __name__ == "__main__":
    generate_capital_vs_duration_heatmap()
