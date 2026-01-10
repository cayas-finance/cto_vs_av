import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.colors import TwoSlopeNorm

from enveloppes.succession.stochastic import calculer_heritage_stochastique
from enveloppes.core.fiscalite import get_regime_successoral

def run_dual_stochastic_heatmap():
    print("Génération de la heatmap stochastique double (rendement vs rotation)...")
    
    # Paramètres alignés sur stochastic_comparison.py
    capital_initial = 100_000
    duree = 30
    vol = 0.15 # Volatilité moyenne
    frais_av = 0.005
    frais_sociaux = 0.172
    nb_sims = 300 # Réduit pour accélérer la génération
    seed = 42
    
    # Grille
    resol = 12
    yields = np.linspace(0.02, 0.10, resol) # 2% à 10%
    turnovers = np.linspace(0.0, 0.20, resol) # 0% à 20%
    
    # Scénario 1 : abattement déjà consommé (300k d'actifs existants)
    autres_biens_1 = 300_000
    
    # Scénario 2 : abattement disponible (0 actif existant)
    autres_biens_2 = 0
    
    # Régime successoral
    ab_h, bar_h = get_regime_successoral("ligne_directe")
    ab_av_total = 152_500 
    bar_av = [(700_000, 0.20), (np.inf, 0.3125)]
    
    Z1 = np.zeros((resol, resol))
    Z2 = np.zeros((resol, resol))
    
    print("Calcul de la grille...")
    for i, to in enumerate(turnovers):
        for j, yld in enumerate(yields):
            # Scénario 1
            res1 = calculer_heritage_stochastique(
                capital_initial, duree, yld, vol,
                frais_av, frais_sociaux,
                autres_biens_1, ab_h, bar_h,
                ab_av_total, bar_av,
                taux_rotation=to, nb_trajectoires=nb_sims, seed=seed
            )
            total_av_1 = res1['av_total']
            total_cto_1 = res1['cto_total']
            max_total_1 = np.maximum(total_av_1, total_cto_1)
            diff_rel_1 = np.where(
                max_total_1 > 0,
                (total_av_1 - total_cto_1) / max_total_1 * 100,
                0.0,
            )
            Z1[i, j] = np.mean(diff_rel_1)
            
            # Scénario 2
            res2 = calculer_heritage_stochastique(
                capital_initial, duree, yld, vol,
                frais_av, frais_sociaux,
                autres_biens_2, ab_h, bar_h,
                ab_av_total, bar_av,
                taux_rotation=to, nb_trajectoires=nb_sims, seed=seed
            )
            total_av_2 = res2['av_total']
            total_cto_2 = res2['cto_total']
            max_total_2 = np.maximum(total_av_2, total_cto_2)
            diff_rel_2 = np.where(
                max_total_2 > 0,
                (total_av_2 - total_cto_2) / max_total_2 * 100,
                0.0,
            )
            Z2[i, j] = np.mean(diff_rel_2)

    # Tracé côte à côte
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharey=True)
    
    # Étendue commune
    ext = [yields[0]*100, yields[-1]*100, turnovers[0]*100, turnovers[-1]*100]
    
    # Tracé 1
    im1 = axes[0].imshow(
        Z1, origin='lower', extent=ext, aspect='auto', cmap='RdYlGn'
    )
    axes[0].set_title("Scénario A : Abattement successoral consommé\n(Patrimoine hors enveloppe = 300k€)")
    axes[0].set_xlabel("Rendement espéré (%)")
    axes[0].set_ylabel("Taux de rotation annuel (%)")
    axes[0].contour(yields*100, turnovers*100, Z1, levels=[0], colors='black', linewidths=2, linestyles='-')
    
    # Tracé 2
    im2 = axes[1].imshow(
        Z2, origin='lower', extent=ext, aspect='auto', cmap='RdYlGn'
    )
    axes[1].set_title("Scénario B : Abattement successoral disponible\n(Patrimoine hors enveloppe = 0€)")
    axes[1].set_xlabel("Rendement espéré (%)")
    # axes[1].set_ylabel("Taux de Rotation Annuel (%)")
    axes[1].contour(yields*100, turnovers*100, Z2, levels=[0], colors='black', linewidths=2, linestyles='-')

    cbar = fig.colorbar(
        im2,
        ax=axes.ravel().tolist(),
        label="Avantage relatif moyen (%) : vert=AV, rouge=CTO",
    )
    
    plt.suptitle("Avantage relatif moyen AV vs CTO (Horizon 30 ans, Volatilité 15%)", fontsize=16)
    
    output_path = os.path.join(os.path.dirname(__file__), '../images/stochastic_dual_scenario.png')
    # Assure l'existence du dossier de sortie
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Enregistré : {output_path}")

if __name__ == "__main__":
    run_dual_stochastic_heatmap()
