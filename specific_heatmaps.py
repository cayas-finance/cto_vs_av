
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from CTO_vs_AV import (
    calculer_heritage_assurance_vie,
    calculer_heritage_cto,
    get_regime_successoral
)

def plot_heatmap(Z, x_range, y_range, x_label, y_label, title, filename):
    plt.figure(figsize=(10, 8))
    
    vmin = np.min(Z)
    vmax = np.max(Z)
    
    # Force the range to include 0 to ensure Red=Negative / Green=Positive consistency
    # If all values are negative, set vmax=0 (or slightly above to avoid singularity)
    # If all values are positive, set vmin=0
    
    # To assure proper centering:
    div_norm_min = min(vmin, -1.0)
    div_norm_max = max(vmax, 1.0)
    
    norm = TwoSlopeNorm(vmin=div_norm_min, vcenter=0, vmax=div_norm_max)
    
    # If Y axis is inverted (Fees), we handle it in data prep or plotting
    # Imshow plots from top-down by default unless origin='lower'
    
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
    print("Generating Specific Heatmaps (Relative %)...")
    resol = 200
    
    # Common Params
    frais_sociaux = 0.172
    abattement_av_total = 152_500 # 1 benef
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    abattement_par_heritier, bareme_succ = get_regime_successoral("ligne_directe")
    abattement_succ_total = abattement_par_heritier # 1 benef
    autres_biens = 300_000 # Consommation abatement
    
    # --- 1. Impact Frais vs Durée (Capital 100k, Yield 5%) ---
    durations = np.linspace(1, 40, resol)
    fees = np.linspace(0.00, 0.02, resol) # 0% to 2%
    Z1 = np.zeros((resol, resol))
    
    cap = 100_000
    yld = 0.05
    
    for i, fee in enumerate(fees): # Y axis
        for j, dur in enumerate(durations): # X axis
            av = calculer_heritage_assurance_vie(cap, dur, yld, fee, frais_sociaux, abattement_av_total, bareme_av).heritage_net
            cto = calculer_heritage_cto(cap, dur, yld, autres_biens, abattement_succ_total, bareme_succ).heritage_net
            
            # Relative difference in % of CTO result
            # If CTO wins, diff is negative %. If AV wins, diff is positive %.
            if cto > 0:
                Z1[i, j] = (av - cto) / cto * 100.0
            else:
                Z1[i, j] = 0.0
            
    plot_heatmap(Z1, durations, fees*100, "Durée (Années)", "Frais de Gestion AV (%)", 
                 "1. Impact des Frais AV (Relatif %)", "heatmap_frais_duree.png")

    # --- 2. Impact Rendement vs Durée (Capital 100k, Frais 0.6%) ---
    yields = np.linspace(0.01, 0.12, resol) # 1% to 12%
    Z2 = np.zeros((resol, resol))
    fee_fixed = 0.006
    
    for i, y in enumerate(yields): 
        for j, dur in enumerate(durations):
            av = calculer_heritage_assurance_vie(cap, dur, y, fee_fixed, frais_sociaux, abattement_av_total, bareme_av).heritage_net
            cto = calculer_heritage_cto(cap, dur, y, autres_biens, abattement_succ_total, bareme_succ).heritage_net
            if cto > 0:
                Z2[i, j] = (av - cto) / cto * 100.0
            else:
                Z2[i, j] = 0.0
            
    plot_heatmap(Z2, durations, yields*100, "Durée (Années)", "Rendement Brut (%)", 
                 "2. Impact Rendement (Relatif %)", "heatmap_rendement_duree.png")

    # --- 3. Petit Patrimoine: Capital vs Frais (Durée 20 ans, Yield 5%) ---
    # Ici on met autres_biens = 0 pour voir l'effet des abattements bas
    capitals = np.linspace(10_000, 150_000, resol)
    fees_av = np.linspace(0.00, 0.02, resol)
    Z3 = np.zeros((resol, resol))
    dur_fixed = 20
    yld_fixed = 0.05
    
    for i, fee in enumerate(fees_av):
        for j, c in enumerate(capitals):
            av = calculer_heritage_assurance_vie(c, dur_fixed, yld_fixed, fee, frais_sociaux, abattement_av_total, bareme_av).heritage_net
            cto = calculer_heritage_cto(c, dur_fixed, yld_fixed, 0, abattement_succ_total, bareme_succ).heritage_net
            if cto > 0:
                Z3[i, j] = (av - cto) / cto * 100.0
            else:
                Z3[i, j] = 0.0
            
    plot_heatmap(Z3, capitals/1000, fees_av*100, "Capital (k€)", "Frais de Gestion AV (%)", 
                 "3. Petit Patrimoine (Relatif %)", "heatmap_capital_frais.png")

if __name__ == "__main__":
    run()
