import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

from enveloppes.core.fiscalite import calculate_succession_tax_marginal
from enveloppes.envelopes.cto import CTOSimulation
from enveloppes.envelopes.av import AVSimulation
from enveloppes.core.fiscalite import calcul_emoluments_notaire

def run_accident_heatmap():
    print("Génération de la heatmap accident (rendement vs année d'accident)...")
    
    # Plages
    # Années d'accident entières
    accident_years = np.arange(1, 30) # 1 à 29
    resol_y = len(accident_years)
    
    resol_x = 200
    yields = np.linspace(0.02, 0.12, resol_x) # 2% à 12%
    
    # Paramètres fixes
    cap_ini = 100_000
    total_duration = 30
    fees_av = 0.005
    autres_biens = 300_000 
    
    Z = np.zeros((resol_y, resol_x))
    
    for i, acc_year in enumerate(accident_years): # Axe Y
        for j, yld in enumerate(yields): # Axe X
            
            # --- CTO avec accident ---
            sim_cto = CTOSimulation(cap_ini, yld)
            for year in range(total_duration):
                if year == acc_year:
                    sim_cto.force_liquidation_tax_event() # Accident
                sim_cto.advance_one_year()
                
            # Succession
            # La purge s'applique aux gains finaux (post-accident)
            tax_cto = calculate_succession_tax_marginal(sim_cto.capital, autres_biens)
            notary_fees_cto = calcul_emoluments_notaire(sim_cto.capital)
            net_cto = sim_cto.capital - tax_cto - notary_fees_cto
            
            # --- AV (accident neutre) ---
            sim_av = AVSimulation(cap_ini, yld, frais_gestion_av=fees_av)
            for year in range(total_duration):
                # L'accident n'a pas d'effet en AV (arbitrage)
                if year == acc_year:
                    sim_av.force_liquidation_tax_event()
                sim_av.advance_one_year()
                
            # Succession
            gains_succ = max(0, sim_av.capital - sim_av.total_versements)
            ps_succ = gains_succ * 0.172
            base_taxable_av = max(0, sim_av.capital - ps_succ - 152_500)
            tax_av = 0.0
            if base_taxable_av > 0:
                tax_av = base_taxable_av * 0.20
            net_av = sim_av.capital - ps_succ - tax_av
            
            # Net des autres biens
            tax_autres_only = calculate_succession_tax_marginal(0, autres_biens)
            net_autres = autres_biens - tax_autres_only
            
            total_av_global = net_av + net_autres
            total_cto_global = net_cto + net_autres
            
            max_global = max(total_av_global, total_cto_global)

            # Comparaison
            if max_global > 0:
                Z[i, j] = (total_av_global - total_cto_global) / max_global * 100.0
            else:
                 Z[i, j] = 0.0
                 
    plt.figure(figsize=(12, 10))
    norm = TwoSlopeNorm(vmin=min(np.min(Z), -2), vcenter=0, vmax=max(np.max(Z), 2))
    
    # Imshow avec interpolation bicubique
    plt.imshow(
        Z, 
        origin='lower', 
        extent=[yields[0]*100, yields[-1]*100, accident_years[0], accident_years[-1]], 
        aspect='auto',
        cmap='RdYlGn', 
        norm=norm,
        interpolation='bicubic'
    )
    plt.colorbar(label="Avantage relatif (%) : vert = AV, rouge = CTO")
    plt.xlabel("Rendement annuel (%)")
    plt.ylabel("Année de l'accident (sur 30 ans)")
    plt.title(f"Scénario accident : impact d'une vente forcée (CTO vs AV)")
    
    plt.contour(yields*100, accident_years, Z, levels=[0], colors='black', linestyles='dashed')

    output_path = os.path.join(os.path.dirname(__file__), '../images/heatmap_accident.png')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Enregistré : {output_path}")

if __name__ == "__main__":
    run_accident_heatmap()
