
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from advanced_simulation import SimulationEngine, calculate_succession_tax_marginal

def run_accident_heatmap():
    print("Generating Accident Heatmap (Yield vs Accident Year)...")
    
    # Ranges
    # Integers for accident year
    accident_years = np.arange(1, 30) # 1 to 29
    resol_y = len(accident_years)
    
    resol_x = 200
    yields = np.linspace(0.02, 0.12, resol_x) # 2% to 12%
    
    # Fixed Params
    cap_ini = 100_000
    total_duration = 30
    fees_av = 0.005
    autres_biens = 300_000 
    
    Z = np.zeros((resol_y, resol_x))
    
    for i, acc_year in enumerate(accident_years): # Y axis
        for j, yld in enumerate(yields): # X axis
            
            # --- CTO with Accident ---
            sim_cto = SimulationEngine(cap_ini, yld, 0)
            for year in range(total_duration):
                if year == acc_year:
                    sim_cto.force_liquidation_tax_event('CTO') # The accident
                sim_cto.advance_one_year()
                
            # Succession
            # Purge applies to the final gains (post-accident)
            tax_cto = calculate_succession_tax_marginal(sim_cto.capital, autres_biens)
            net_cto = sim_cto.capital - tax_cto
            
            # --- AV (Accident is neutral) ---
            sim_av = SimulationEngine(cap_ini, yld, fees_av)
            for year in range(total_duration):
                # Accident does nothing in AV (arbitrage)
                if year == acc_year:
                    sim_av.force_liquidation_tax_event('AV') 
                sim_av.advance_one_year()
                
            # Succession
            gains_succ = max(0, sim_av.capital - sim_av.total_versements)
            ps_succ = gains_succ * 0.172
            base_taxable_av = max(0, sim_av.capital - ps_succ - 152_500)
            tax_av = 0.0
            if base_taxable_av > 0:
                tax_av = base_taxable_av * 0.20
            net_av = sim_av.capital - ps_succ - tax_av
            
            # Comparison
            if net_cto > 0:
                Z[i, j] = (net_av - net_cto) / net_cto * 100.0
            else:
                 Z[i, j] = 0.0
                 
    plt.figure(figsize=(12, 10))
    norm = TwoSlopeNorm(vmin=min(np.min(Z), -2), vcenter=0, vmax=max(np.max(Z), 2))
    
    # Use imshow with bicubic interpolation
    plt.imshow(
        Z, 
        origin='lower', 
        extent=[yields[0]*100, yields[-1]*100, accident_years[0], accident_years[-1]], 
        aspect='auto',
        cmap='RdYlGn', 
        norm=norm,
        interpolation='bicubic'
    )
    plt.colorbar(label="Avantage Global (%) : Vert = AV, Rouge = CTO")
    plt.xlabel("Rendement Annuel (%)")
    plt.ylabel("Année de l'Accident (sur 30 ans)")
    plt.title(f"Scénario Accident : Impact d'une vente forcée (CTO vs AV)")
    
    plt.contour(yields*100, accident_years, Z, levels=[0], colors='black', linestyles='dashed')

    filename = "heatmap_accident.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved {filename}")

if __name__ == "__main__":
    run_accident_heatmap()
