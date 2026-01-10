import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import os

from enveloppes.succession.heritage import calculer_heritage_assurance_vie, calculer_heritage_cto
from enveloppes.core.fiscalite import get_regime_successoral

def generate_profile_heatmap(yield_val, filename, title, frais_av=0.005):
    print(f"Génération de la heatmap : {title} (rendement {yield_val:.0%}, frais AV {frais_av:.2%})...")
    
    # Paramètres de grille
    resol_x = 50 # Durée
    resol_y = 50 # Capital
    
    durations = np.linspace(10, 50, resol_x)
    # 100k à 15M
    capitals = np.geomspace(100_000, 15_000_000, resol_y) 
    
    # Paramètres fixes
    autres_biens = 300_000 
    nb_beneficiaires = 2
    # frais_av passé en argument
    frais_sociaux = 0.172
    versement_apres_70 = False 
    
    # Grille de sortie
    Z = np.zeros((resol_y, resol_x))
    
    # Pré-calcul des paramètres successoraux
    abattement_av_total = 152_500 * nb_beneficiaires
    bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    abattement_par_heritier, bareme_succession = get_regime_successoral("ligne_directe")
    abattement_succession_total = abattement_par_heritier * nb_beneficiaires
    
    for i, cap in enumerate(capitals):
        for j, dur in enumerate(durations):
            # Résultat AV
            av_res = calculer_heritage_assurance_vie(
                cap, dur, yield_val, frais_av, frais_sociaux,
                abattement_av_total, bareme_av,
                versement_apres_70=versement_apres_70
            )
            # Résultat CTO
            cto_res = calculer_heritage_cto(
                cap, dur, yield_val, autres_biens,
                abattement_succession_total, bareme_succession
            )
            
            # Métrique : avantage en % du net total (enveloppe + autres biens)
            # 1. Net des autres biens
            base_taxable_autres = max(0, autres_biens - abattement_succession_total)
            droits_autres = 0.0
            prev = 0.0
            for plaf, tx in bareme_succession:
                d = min(base_taxable_autres, plaf) - prev
                if d > 0:
                    droits_autres += d * tx
                    prev = min(base_taxable_autres, plaf)
            net_autres = autres_biens - droits_autres

            total_av_global = av_res.heritage_net + net_autres
            
            # Total CTO global : net CTO + autres biens après droits globaux
            droits_autres = cto_res.droits_totaux - cto_res.droits_imputes_cto
            total_cto_global = cto_res.heritage_net + autres_biens - droits_autres

            # Comparaison
            net_gagnant = max(total_av_global, total_cto_global)
            
            # 3. Nouvelle formule
            diff = total_av_global - total_cto_global 
            diff_rel = (diff / net_gagnant) * 100 if net_gagnant > 0 else 0
            Z[i, j] = diff_rel

    # Tracé
    plt.figure(figsize=(12, 8))
    
    # Normalisation de la palette : 0 = blanc (neutre)
    v_min, v_max = np.min(Z), np.max(Z)
    vlimit = max(abs(v_min), abs(v_max))
    if vlimit < 1e-5: vlimit = 1.0
    
    ext = [durations[0], durations[-1], 0, resol_y-1]
    
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
    # Valeurs à afficher
    round_caps = [100_000, 500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000, 15_000_000]
    
    # Indices les plus proches dans la geomspace
    tick_indices = []
    tick_labels = []
    for rc in round_caps:
        # Indice de la valeur la plus proche
        idx = (np.abs(capitals - rc)).argmin()
        tick_indices.append(idx)
        # Format du label
        if rc >= 1_000_000:
            label = f"{rc/1e6:g} M€"
        else:
            label = f"{int(rc/1000)} k€"
        tick_labels.append(label)

    plt.yticks(tick_indices, tick_labels)
    
    plt.colorbar(im, label="Avantage relatif (%) : vert = AV, rouge = CTO")
    plt.xlabel("Durée de détention (années)")
    plt.ylabel("Capital initial")
    plt.title(title)
    
    # Sauvegarde
    if not os.path.exists('images'):
        os.makedirs('images')
    
    plt.savefig(os.path.join('images', filename))
    plt.close()

if __name__ == "__main__":
    profiles = [
        # (Rendement, nom de fichier, titre, frais)
        (0.03, "heatmap_tipping_point_3pct.png", "Profil Prudent (3 %) : AV 0.5% frais", 0.005),
        (0.05, "heatmap_tipping_point_5pct.png", "Profil Équilibré (5 %) : AV 0.5% frais", 0.005),
        (0.08, "heatmap_tipping_point.png", "Profil Dynamique (8 %) : AV 0.5% frais", 0.005),
    ]
    
    for yld, fname, title, fees in profiles:
        generate_profile_heatmap(yld, fname, title, frais_av=fees)
