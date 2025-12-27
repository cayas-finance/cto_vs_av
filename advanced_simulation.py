
import numpy as np

class SimulationEngine:
    def __init__(self, capital_initial, rendement, frais_gestion_av=0.0):
        self.capital = capital_initial
        self.total_versements = capital_initial # Pour AV (assiette 757B et produits)
        self.prix_revient_cto = capital_initial # Pour CTO (PRU)
        self.rendement = rendement
        self.frais_gestion_av = frais_gestion_av
        self.age_contrat = 0
        
    def advance_one_year(self):
        # 1. Rendement brut
        gain = self.capital * self.rendement
        self.capital += gain
        
        # 2. Frais de gestion (AV uniquement)
        frais = self.capital * self.frais_gestion_av
        self.capital -= frais
        
        self.age_contrat += 1

    def withdraw(self, amount_gross, envelope_type, abattement_av_annuel=4600):
        """
        Retire 'amount_gross' du compte.
        Calcule la fiscalité immédiate (IR/PS) payée par l'investisseur (hors du compte).
        Met à jour le PRU / Total Versements.
        Returns: net_in_pocket
        """
        if self.capital <= 0:
            return 0.0

        ratio_gains = max(0, (self.capital - self.total_versements) / self.capital) if envelope_type == 'AV' else \
                      max(0, (self.capital - self.prix_revient_cto) / self.capital)
        
        part_gains = amount_gross * ratio_gains
        part_capital = amount_gross - part_gains
        
        self.capital -= amount_gross
        
        tax = 0.0
        
        if envelope_type == 'CTO':
            # Flat Tax 30% sur les gains
            tax = part_gains * 0.30
            # Mise à jour PRU : on a sorti 'part_capital' du PRU
            self.prix_revient_cto -= part_capital
            
        elif envelope_type == 'AV':
            # AV : PS 17.2% + IR
            # PS
            ps = part_gains * 0.172
            
            # IR : Abattement 4600€ après 8 ans (supposons > 8 ans pour simplifier ou check age)
            # Scenario user: investit à 50 ans, retire à 70 ans -> > 8 ans.
            assiette_ir = part_gains
            if self.age_contrat >= 8:
                assiette_ir = max(0, part_gains - abattement_av_annuel)
            
            # Taux 7.5% (si < 150k versements, hypothese simplificatrice ok ici) ou 12.8%
            # On prend 7.5% (cas standard optimisé)
            ir = assiette_ir * 0.075
            
            tax = ps + ir
            
            # Update Versements (Part capital sortie)
            self.total_versements -= part_capital
            
        return amount_gross - tax

    def force_liquidation_tax_event(self, envelope_type):
        """
        Simule une vente forcée totale suivie d'un réinvestissement.
        CTO: Taxe les PV latentes à 30%, le net est réinvesti (nouveau PRU = Montant).
        AV: Neutre (arbitrage).
        """
        if envelope_type == 'AV':
            return # Transparent
            
        elif envelope_type == 'CTO':
            pv_latente = max(0, self.capital - self.prix_revient_cto)
            tax = pv_latente * 0.30
            
            self.capital -= tax # On paie la taxe avec le capital
            self.prix_revient_cto = self.capital # Reset PRU (on vient de racheter)
            
    def get_succession_net(self, envelope_type, nb_benef=1):
        """
        Calcule le net après succession.
        """
        final_capital = self.capital
        
        if envelope_type == 'CTO':
            # Purge des PV latentes : 0 taxe sur gains.
            # Droits de succession sur la valeur totale
            # Hypothese : Heritage Ligne Directe, autres biens consomment l'abattement
            # On applique le barème marginalement
            # Simplification : Taux moyen environ 20% sur 200-300k, ou marginal 20%.
            # Pour etre précis, il faudrait le barème complet.
            # On va utiliser une fonction simplifiée ou appeler celle de CTO_vs_AV si possible
            # Ici pour les "Case Studies", on va hardcoder un contexte fiscal "Moyen" (20% marginal)
            # Ou mieux : réutiliser la logique précise.
            pass
            
        # ... actually let's defer this to the main script using CTO_vs_AV helpers
        return final_capital

# --- Simulation Script ---
from CTO_vs_AV import get_regime_successoral, calcul_impot_progressif

def calculate_succession_tax_marginal(masse_taxable, autres_biens, regime_code="ligne_directe", nb_benef=1):
    abattement, bareme = get_regime_successoral(regime_code)
    abattement_total = abattement * nb_benef
    
    # Impot sur autres biens
    base_autres = max(0, autres_biens - abattement_total)
    tax_autres = calcul_impot_progressif(base_autres, bareme)
    
    # Impot total
    base_total = max(0, autres_biens + masse_taxable - abattement_total)
    tax_total = calcul_impot_progressif(base_total, bareme)
    
    return tax_total - tax_autres

def run_scenarios():
    print("=== SCENARIO 1: RENTE / RETRAITS (The 'Fire' Case) ===")
    # 100k à 50 ans. 5%/an.
    # Accumulation 20 ans (-> 70 ans).
    # Retrait 5000€/an de 70 à 80 ans (10 ans).
    # Décès à 80 ans.
    
    cap_ini = 100_000
    yield_val = 0.05
    fees_av = 0.005
    withdrawal = 5000
    
    # --- CTO ---
    sim_cto = SimulationEngine(cap_ini, yield_val, 0)
    # Phase 1: Accumulation 20y
    for _ in range(20): sim_cto.advance_one_year()
    capital_at_70_cto = sim_cto.capital
    
    # Phase 2: Withdrawal 10y
    total_net_withdrawals_cto = 0
    for _ in range(10):
        net = sim_cto.withdraw(withdrawal, 'CTO')
        total_net_withdrawals_cto += net
        sim_cto.advance_one_year()
        
    capital_at_80_cto = sim_cto.capital
    
    # Succession CTO
    # Purge PV : Assiette = Capital Final
    tax_succ_cto = calculate_succession_tax_marginal(capital_at_80_cto, 300_000, "ligne_directe")
    net_heir_cto = capital_at_80_cto - tax_succ_cto
    
    print(f"CTO -> Cap 70ans: {capital_at_70_cto:,.0f}")
    print(f"CTO -> Total Net Retraits: {total_net_withdrawals_cto:,.0f} (Brut retiré: {withdrawal*10})")
    print(f"CTO -> Cap Final Décès: {capital_at_80_cto:,.0f}")
    print(f"CTO -> Taxe Succ: {tax_succ_cto:,.0f}")
    print(f"CTO -> NET HEIR: {net_heir_cto:,.0f}")
    print(f"TOTAL VALUE (Heir + Withdrawals): {net_heir_cto + total_net_withdrawals_cto:,.0f}")

    print("\n")
    
    # --- AV ---
    sim_av = SimulationEngine(cap_ini, yield_val, fees_av)
    for _ in range(20): sim_av.advance_one_year()
    capital_at_70_av = sim_av.capital
    
    total_net_withdrawals_av = 0
    for _ in range(10):
        # Abattement annual 4600 applying
        net = sim_av.withdraw(withdrawal, 'AV', abattement_av_annuel=4600)
        total_net_withdrawals_av += net
        sim_av.advance_one_year()
        
    capital_at_80_av = sim_av.capital
    
    # Succession AV (< 70 ans versés)
    # Assiette Taxable = Capital Final - PS (17.2% sur gains) - Abattement (152500)
    # Gains calculation
    # Attention: gains succession != gains rachat because 'versements' tracked carefully?
    # Actually for Succ: Gain = Val - Primes.
    # SimulationEngine tracks total_versements correctly assuming withdrawals remove proportional capital.
    gains_succ = max(0, sim_av.capital - sim_av.total_versements)
    ps_succ = gains_succ * 0.172
    base_taxable_av = max(0, sim_av.capital - ps_succ - 152_500) # 1 benef
    tax_av = 0.0 # < 152k usually free, lets compute real
    if base_taxable_av > 0:
        tax_av = base_taxable_av * 0.20 # Simplified bracket
        
    net_heir_av = sim_av.capital - ps_succ - tax_av
    
    print(f"AV  -> Cap 70ans: {capital_at_70_av:,.0f}")
    print(f"AV  -> Total Net Retraits: {total_net_withdrawals_av:,.0f}")
    print(f"AV  -> Cap Final Décès: {capital_at_80_av:,.0f}")
    print(f"AV  -> PS Succ: {ps_succ:,.0f} | Tax Succ: {tax_av:,.0f}")
    print(f"AV  -> NET HEIR: {net_heir_av:,.0f}")
    print(f"TOTAL VALUE (Heir + Withdrawals): {net_heir_av + total_net_withdrawals_av:,.0f}")
    
    
    print("\n=== SCENARIO 2: ACCIDENT (Forced Sale at 20y) ===")
    # 200k Init, 30y total duration. Accident at year 20.
    cap_ini = 200_000
    yield_val = 0.08 # High yield accentuates the pain of tax event
    fees_av = 0.005
    duration = 30
    accident_year = 20
    
    # --- CTO Normal (No Accident) ---
    sim = SimulationEngine(cap_ini, yield_val, 0)
    for _ in range(duration): sim.advance_one_year()
    # Succession
    tax = calculate_succession_tax_marginal(sim.capital, 300_000)
    net_normal = sim.capital - tax
    
    # --- CTO Accident ---
    sim_acc = SimulationEngine(cap_ini, yield_val, 0)
    for y in range(duration):
        if y == accident_year:
            sim_acc.force_liquidation_tax_event('CTO')
        sim_acc.advance_one_year()
    # Succession
    # Note: PRU is high (reset at year 20), but Purge doesn't care about PRU.
    # Purge erases tax on gains regardless.
    # The cost is the LOST CAPITAL paid in tax at year 20 that didn't compound for last 10 years.
    tax_acc = calculate_succession_tax_marginal(sim_acc.capital, 300_000)
    net_acc = sim_acc.capital - tax_acc
    
    # --- AV (Accident is neutral) ---
    sim_av = SimulationEngine(cap_ini, yield_val, fees_av)
    for y in range(duration):
        if y == accident_year:
            sim_av.force_liquidation_tax_event('AV') # Does nothing
        sim_av.advance_one_year()
    # Succ
    gains = max(0, sim_av.capital - sim_av.total_versements)
    ps = gains * 0.172
    base = max(0, sim_av.capital - ps - 152_500)
    tax_av = base * 0.20 # Simplified
    net_av = sim_av.capital - ps - tax_av
    
    print(f"Yield: {yield_val*100}%")
    print(f"CTO Standard Net: {net_normal:,.0f}")
    print(f"CTO Accident Net: {net_acc:,.0f}")
    print(f"Perte due à l'accident CTO: {net_normal - net_acc:,.0f}")
    print(f"AV Net: {net_av:,.0f}")

original_run_scenarios = run_scenarios
if __name__ == "__main__":
    run_scenarios()
