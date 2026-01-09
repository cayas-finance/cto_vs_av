import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Ajoute le dossier racine pour permettre les imports depuis src

from cto_av_comp.model import (
    get_regime_successoral,
    calcul_impot_progressif,
    calcul_emoluments_notaire
)

def simulate_complex_diversified_portfolio():
    # Paramètres des actifs
    # NTSG : levier 90/60. Rendement attendu ~8,5%, vol ~14%
    # Managed Futures (MF) : suivi de tendance. Rendement ~5,5%, vol ~11%
    # Or : rendement ~4,5%, vol ~16%
    assets_meta = {
        'NTSG': {'yield': 0.085, 'vol': 0.14, 'target_weight': 0.80},
        'MF':   {'yield': 0.055, 'vol': 0.11, 'target_weight': 0.10},
        'Gold': {'yield': 0.045, 'vol': 0.16, 'target_weight': 0.10}
    }
    
    asset_names = ['NTSG', 'MF', 'Gold']
    yields = np.array([assets_meta[n]['yield'] for n in asset_names])
    vols = np.array([assets_meta[n]['vol'] for n in asset_names])
    target_weights = np.array([assets_meta[n]['target_weight'] for n in asset_names])
    
    # Paramètres globaux
    capital_initial = 100_000
    duree = 30
    nb_trajectories = 5000
    frais_av = 0.005
    flat_tax = 0.312
    seed = 42
    
    # Contexte successoral (ligne directe, 300k d'actifs existants)
    autres_biens = 300_000
    ab_h, bar_h = get_regime_successoral("ligne_directe")
    ab_av = 152_500
    bar_av = [(700_000, 0.20), (np.inf, 0.3125)]
    
    # Matrice de corrélation (effet de diversification)
    # NTSG, MF, Or
    corrs = np.array([
        [1.0, -0.1, 0.1],
        [-0.1, 1.0, 0.2],
        [0.1, 0.2, 1.0]
    ])
    
    cov_matrix = np.outer(vols, vols) * corrs
    
    heritages_cto = []
    heritages_av = []
    total_turnovers = []
    
    np.random.seed(seed)
    
    for _ in range(nb_trajectories):
        # État CTO
        vals_cto = capital_initial * target_weights
        prus_cto = vals_cto.copy()
        
        # État AV (frais annuels)
        val_av = capital_initial
        
        sim_turnover_sum = 0
        
        # Simulation des rendements
        multi_normals = np.random.multivariate_normal(np.zeros(3), corrs, duree)
        
        for t in range(duree):
            # 1. Simulation des rendements
            # Mouvement brownien géométrique
            # r = exp((mu - 0.5*sigma^2) + sigma*Z) - 1
            z = multi_normals[t]
            rs = np.exp((yields - 0.5 * vols**2) + vols * z) - 1
            
            # 2. Mise à jour des valeurs
            vals_cto *= (1 + rs)
            total_cto = np.sum(vals_cto)
            
            # --- RÉÉQUILIBRAGE CTO ---
            target_vals = total_cto * target_weights
            diffs = vals_cto - target_vals # > 0 means sell
            
            # Rééquilibrage : vendre les gagnants pour acheter les perdants
            if np.any(np.abs(diffs) > 1e-6):
                turnover_fraction = np.sum(np.abs(diffs)) / (2 * total_cto)
                sim_turnover_sum += turnover_fraction
                
                # Identification des vendeurs et acheteurs
                sellers_idx = np.where(diffs > 0)[0]
                buyers_idx = np.where(diffs < 0)[0]
                
                tax_total = 0
                for idx in sellers_idx:
                    selling_amount = diffs[idx]
                    ratio_gain = max(0, (vals_cto[idx] - prus_cto[idx]) / vals_cto[idx])
                    tax = selling_amount * ratio_gain * flat_tax
                    tax_total += tax
                    
                    # Mise à jour du PRU (réduction)
                    prus_cto[idx] -= (selling_amount * (prus_cto[idx] / vals_cto[idx]))
                    vals_cto[idx] -= selling_amount
                
                # Redistribution du cash restant après impôt
                total_to_buy = np.sum(np.abs(diffs[sellers_idx])) - tax_total
                
                # Achat fractionné pour chaque acheteur
                # Les écarts donnent les montants cibles, avec frottement fiscal.
                buy_requests = np.abs(diffs[buyers_idx])
                sum_buy_requests = np.sum(buy_requests)
                
                for idx_in_buyers, idx in enumerate(buyers_idx):
                    buy_amount = (buy_requests[idx_in_buyers] / sum_buy_requests) * total_to_buy
                    vals_cto[idx] += buy_amount
                    prus_cto[idx] += buy_amount
            
            # --- Avancement AV ---
            # Le rééquilibrage en AV est neutre fiscalement.
            r_portfolio = np.sum(target_weights * rs)
            val_av = val_av * (1 + r_portfolio - frais_av)
            
        # Fin de simulation : succession
        total_turnovers.append(sim_turnover_sum / duree)
        
        # Net CTO
        total_final_cto = np.sum(vals_cto)
        total_pat_cto = total_final_cto + autres_biens
        tax_total_cto = calcul_impot_progressif(max(0, total_pat_cto - ab_h), bar_h)
        tax_ext_cto = calcul_impot_progressif(max(0, autres_biens - ab_h), bar_h)
        notary_fees_cto = calcul_emoluments_notaire(total_final_cto)
        heritage_cto_res = total_final_cto - (tax_total_cto - tax_ext_cto) - notary_fees_cto
        heritages_cto.append(heritage_cto_res)
        
        # Net AV
        plus_value_av = max(0, val_av - capital_initial)
        ps_av = plus_value_av * 0.172
        cap_apres_ps = val_av - ps_av
        tax_av = calcul_impot_progressif(max(0, cap_apres_ps - ab_av), bar_av)
        tax_av = calcul_impot_progressif(max(0, cap_apres_ps - ab_av), bar_av)
        heritages_av.append(cap_apres_ps - tax_av)

    # Calcul du net des autres biens (contexte fixe)
    tax_autres = calcul_impot_progressif(max(0, autres_biens - ab_h), bar_h)
    net_autres = autres_biens - tax_autres
    
    # Calcul des écarts relatifs par trajectoire
    # Formule : ((AV_net + net_autres) - (CTO_net + net_autres)) / max(...)
    diffs_rel = []
    for av, cto in zip(heritages_av, heritages_cto):
        total_av = av + net_autres
        total_cto = cto + net_autres
        m = max(total_av, total_cto)
        if m > 0:
            d = (total_av - total_cto) / m * 100
        else:
            d = 0
        diffs_rel.append(d)
    
    diffs_rel = np.array(diffs_rel)
    mean_diff_rel = np.mean(diffs_rel)
    median_diff_rel = np.median(diffs_rel)

    # Analyse
    avg_turnover = np.mean(total_turnovers)
    prob_av = np.mean(np.array(heritages_av) > np.array(heritages_cto))
    median_av = np.median(heritages_av)
    median_cto = np.median(heritages_cto)
    
    print(f"=== Portefeuille complexe (80% NTSG, 10% MF, 10% Or) ===")
    print(f"Rendement moyen pondéré : {np.sum(target_weights * yields):.2%}")
    print(f"Turnover annuel moyen (rééquilibrage) : {avg_turnover:.2%}")
    print(f"Probabilité AV > CTO : {prob_av:.2%}")
    print(f"Médiane AV : {median_av:,.0f}€")
    print(f"Médiane CTO : {median_cto:,.0f}€")
    print(f"Médiane Advantage Relatif (AV - CTO)% : {median_diff_rel:+.2f}%")
    
    # Tracé de la distribution de l'écart relatif
    plt.figure(figsize=(10, 6))
    plt.hist(diffs_rel, bins=50, alpha=0.7, color='purple', edgecolor='black')
    plt.axvline(0, color='black', linestyle='--', linewidth=2, label='Égalité')
    plt.axvline(median_diff_rel, color='red', linestyle='-', linewidth=2, label=f'Médiane ({median_diff_rel:+.2f}%)')
    
    plt.title(f"Distribution de l'avantage relatif (AV vs CTO)\nStratégie diversifiée 30 ans | Prob AV > CTO : {prob_av:.2%}")
    plt.xlabel("Avantage relatif (% du patrimoine total transmis)")
    plt.ylabel("Fréquence (sur 5000 simulations)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_path = os.path.join('images', 'complex_portfolio_results.png')
    plt.savefig(output_path)
    print(f"Graphique enregistré dans {output_path}")

if __name__ == "__main__":
    if not os.path.exists('images'):
        os.makedirs('images')
    simulate_complex_diversified_portfolio()
