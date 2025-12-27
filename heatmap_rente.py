
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from advanced_simulation import SimulationEngine, calculate_succession_tax_marginal

def run_rente_heatmap():
    print("Generating Rente Heatmap (Yield vs Death Age)...")
    
    # Ranges
    # We compute exactly on integer years for death age to avoid aliasing steps
    death_ages = np.arange(71, 101) # 71 to 100 (30 ints)
    resol_y = len(death_ages)
    
    # Yields are continuous, so we can keep high res
    resol_x = 200
    yields = np.linspace(0.02, 0.10, resol_x) 
    
    # Fixed Params
    cap_ini = 100_000
    start_age = 50
    retire_age = 70
    withdrawal_gross = 5000
    fees_av = 0.005
    autres_biens = 300_000 # Standard
    
    Z = np.zeros((resol_y, resol_x))
    
    for i, death_age in enumerate(death_ages): # Y axis
        # death_age is exactly integer (71, 72...), no rounding step issues
        for j, yld in enumerate(yields): # X axis
            # Simulation Duration
            accum_duration = int(retire_age - start_age)
            withdrawal_duration = int(death_age - retire_age)
            
            # --- CTO ---
            sim_cto = SimulationEngine(cap_ini, yld, 0)
            for _ in range(accum_duration): sim_cto.advance_one_year()
            
            net_withdrawals_cto = 0
            for _ in range(withdrawal_duration):
                net_withdrawals_cto += sim_cto.withdraw(withdrawal_gross, 'CTO')
                sim_cto.advance_one_year()
            
            # Succession
            tax_cto = calculate_succession_tax_marginal(sim_cto.capital, autres_biens)
            net_heir_cto = sim_cto.capital - tax_cto
            total_cto = net_withdrawals_cto + net_heir_cto
            
            # --- AV ---
            sim_av = SimulationEngine(cap_ini, yld, fees_av)
            for _ in range(accum_duration): sim_av.advance_one_year()
            
            net_withdrawals_av = 0
            for _ in range(withdrawal_duration):
                net_withdrawals_av += sim_av.withdraw(withdrawal_gross, 'AV', abattement_av_annuel=4600)
                sim_av.advance_one_year()
                
            # Succession
            gains_succ = max(0, sim_av.capital - sim_av.total_versements)
            ps_succ = gains_succ * 0.172
            base_taxable_av = max(0, sim_av.capital - ps_succ - 152_500)
            tax_av = 0.0
            if base_taxable_av > 0:
                tax_av = base_taxable_av * 0.20
            net_heir_av = sim_av.capital - ps_succ - tax_av
            total_av = net_withdrawals_av + net_heir_av
            
            # Comparison
            if total_cto > 0:
                Z[i, j] = (total_av - total_cto) / total_cto * 100.0
            else:
                 Z[i, j] = 0.0
                 
    plt.figure(figsize=(12, 10))
    norm = TwoSlopeNorm(vmin=min(np.min(Z), -2), vcenter=0, vmax=max(np.max(Z), 2))
    
    # Use imshow with bicubic interpolation to create smoothness from the integer data points
    plt.imshow(
        Z, 
        origin='lower', 
        extent=[yields[0]*100, yields[-1]*100, death_ages[0], death_ages[-1]], 
        aspect='auto',
        cmap='RdYlGn', 
        norm=norm,
        interpolation='bicubic' 
    )
    
    plt.colorbar(label="Avantage Global (%) : Vert = AV, Rouge = CTO")
    plt.xlabel("Rendement Annuel (%)")
    plt.ylabel("Âge au Décès (Début Rente à 70 ans)")
    plt.title(f"Scénario Rente : CTO vs AV (Capital 100k, Retrait 5k/an)")
    
    plt.contour(yields*100, death_ages, Z, levels=[0], colors='black', linestyles='dashed')

    filename = "heatmap_rente.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved {filename}")

if __name__ == "__main__":
    run_rente_heatmap()
