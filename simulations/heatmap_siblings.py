
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import sys
import os

# Ajoute le dossier racine pour permettre les imports depuis src

from cto_av_comp.model import (
    calculer_heritage_assurance_vie,
    calculer_heritage_cto,
    get_regime_successoral
)

def run():
    print("Generating Sibling Transmission Heatmap (5% Yield)...")
    resol = 200
    
    # Plages
    capitals = np.geomspace(100_000, 15_000_000, resol)
    durations = np.linspace(10, 60, resol)
    
    # Paramètres fixes
    rendement = 0.05 
    frais_av = 0.005 # 0,5% (correction de l'hypothèse 9,5%)
    frais_sociaux = 0.172
    nb_benef = 1 # Simulation pour 1 frère/soeur
    
    # AV spécifique fratrie : règle 990 I (152,5k d'abattement puis 20%/31,25%)
    # Avantage majeur vs 35%/45% de droits
    abattement_av_total = 152_500 * nb_benef
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    
    # CTO spécifique fratrie
    abattement_par_heritier, bareme_succ = get_regime_successoral("frere_soeur")
    abattement_succ_total = abattement_par_heritier * nb_benef
    # Hypothèse : autres biens déjà pris en compte.
    # Abattement faible (15k), on fixe une valeur standard.
    autres_biens = 300_000 
    
    Z = np.zeros((resol, resol))
    
    for i, cap in enumerate(capitals): # Axe Y
        for j, dur in enumerate(durations): # Axe X
            av = calculer_heritage_assurance_vie(
                cap, dur, rendement, frais_av, frais_sociaux, 
                abattement_av_total, bareme_av
            ).heritage_net
            
            cto_res = calculer_heritage_cto(
                cap, dur, rendement, autres_biens, 
                abattement_succ_total, bareme_succ
            )
            cto = cto_res.heritage_net
            
            base_taxable_autres = max(0, autres_biens - abattement_succ_total)
            droits_autres = 0.0
            prev_b = 0.0
            d_autres = 0.0
            for plaf, tx in bareme_succ:
                tranche = min(base_taxable_autres, plaf) - prev_b
                if tranche > 0:
                    d_autres += tranche * tx
                    prev_b = min(base_taxable_autres, plaf)
            net_autres = autres_biens - d_autres

            total_av_global = av + net_autres
            
            # Total CTO : net CTO + autres biens après droits globaux
            droits_autres = cto_res.droits_totaux - cto_res.droits_imputes_cto
            total_cto_global = cto_res.heritage_net + autres_biens - droits_autres
            
            max_global = max(total_av_global, total_cto_global)

            if max_global > 0:
                Z[i, j] = (total_av_global - total_cto_global) / max_global * 100.0
            else:
                Z[i, j] = 0.0
    
    # Tracé avec la même logique que les profils
    plt.figure(figsize=(12, 8))
    
    # Normalisation de la palette : 0 = blanc (neutre)
    v_min, v_max = np.min(Z), np.max(Z)
    vlimit = max(abs(v_min), abs(v_max))
    if vlimit < 1e-5: vlimit = 1.0
    
    ext = [durations[0], durations[-1], 0, resol-1]
    
    # Normalisation robuste
    if v_min < 0 < v_max:
        norm = TwoSlopeNorm(vmin=-vlimit, vcenter=0, vmax=vlimit)
    elif v_max <= 0:
        norm = plt.Normalize(vmin=-vlimit, vmax=0)
    else:
        norm = plt.Normalize(vmin=0, vmax=vlimit)

    im = plt.imshow(
        Z, 
        origin='lower', 
        extent=ext, 
        aspect='auto',
        cmap='RdYlGn', 
        norm=norm
    )
    
    # Ajoute la courbe de bascule (Z=0) si elle existe
    if v_min < 0 < v_max:
        plt.contour(Z, levels=[0], colors='black', linewidths=2, extent=ext)
    
    # Ticks arrondis
    tick_indices = []
    tick_labels = []
    round_caps = [100_000, 500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000, 15_000_000]
    for rc in round_caps:
        idx = (np.abs(capitals - rc)).argmin()
        tick_indices.append(idx)
        label = f"{rc/1e6:g} M€" if rc >= 1e6 else f"{int(rc/1000)} k€"
        tick_labels.append(label)

    plt.yticks(tick_indices, tick_labels)
    plt.colorbar(im, label="Avantage relatif (%) : vert = AV, rouge = CTO")
    plt.xlabel("Durée de détention (années)")
    plt.ylabel("Capital initial")
    plt.title(f"Frère/soeur : AV vs CTO (5%/an, frais 0.5%)\nContexte : 300k€ de patrimoine existant")

    output_dir = 'images'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = os.path.join(output_dir, "heatmap_siblings_5pct.png")
    plt.savefig(filename)
    print(f"Enregistré : {filename}")

if __name__ == "__main__":
    run()
