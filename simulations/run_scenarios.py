from cto_av_comp.constants import (
    ABATTEMENT_AV_AVANT_70,
    ABATTEMENT_AV_ANNUEL_INDIVIDUEL,
    BAREME_AV_AVANT_70,
    PS_RATE_AV,
)
from cto_av_comp.model import calcul_emoluments_notaire
from cto_av_comp.simulation_engine import SimulationEngine, calculate_succession_tax_marginal


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
    sim_cto = SimulationEngine(cap_ini, yield_val, 0, envelope_type="CTO")
    # Phase 1 : accumulation 20 ans
    for _ in range(20):
        sim_cto.advance_one_year()
    capital_at_70_cto = sim_cto.capital

    # Phase 2 : retraits 10 ans
    total_net_withdrawals_cto = 0
    for _ in range(10):
        net = sim_cto.withdraw(withdrawal, "CTO")
        total_net_withdrawals_cto += net
        sim_cto.advance_one_year()

    capital_at_80_cto = sim_cto.capital

    # Succession CTO
    # Purge PV : assiette = capital final
    tax_succ_cto = calculate_succession_tax_marginal(capital_at_80_cto, 300_000, "ligne_directe")
    notary_fees_cto = calcul_emoluments_notaire(capital_at_80_cto)
    net_heir_cto = capital_at_80_cto - tax_succ_cto - notary_fees_cto

    print(f"CTO -> Cap 70ans: {capital_at_70_cto:,.0f}")
    print(f"CTO -> Total Net Retraits: {total_net_withdrawals_cto:,.0f} (Brut retiré: {withdrawal*10})")
    print(f"CTO -> Cap Final Décès: {capital_at_80_cto:,.0f}")
    print(f"CTO -> Taxe Succ: {tax_succ_cto:,.0f}")
    print(f"CTO -> NET HEIR: {net_heir_cto:,.0f}")
    print(f"TOTAL VALUE (Heir + Withdrawals): {net_heir_cto + total_net_withdrawals_cto:,.0f}")

    print("\n")

    # --- AV ---
    sim_av = SimulationEngine(cap_ini, yield_val, fees_av, envelope_type="AV")
    for _ in range(20):
        sim_av.advance_one_year()
    capital_at_70_av = sim_av.capital

    total_net_withdrawals_av = 0
    for _ in range(10):
        # Application de l'abattement annuel 4600
        net = sim_av.withdraw(withdrawal, "AV", abattement_av_annuel=ABATTEMENT_AV_ANNUEL_INDIVIDUEL)
        total_net_withdrawals_av += net
        sim_av.advance_one_year()

    capital_at_80_av = sim_av.capital

    # Succession AV (< 70 ans versés)
    # Assiette taxable = capital final - PS (sur gains) - abattement (152500)
    gains_succ = max(0, sim_av.capital - sim_av.total_versements)
    ps_succ = gains_succ * PS_RATE_AV
    base_taxable_av = max(0, sim_av.capital - ps_succ - ABATTEMENT_AV_AVANT_70)  # 1 benef
    tax_av = 0.0  # < 152k, on calcule quand même
    if base_taxable_av > 0:
        tax_av = base_taxable_av * BAREME_AV_AVANT_70[0][1]

    net_heir_av = sim_av.capital - ps_succ - tax_av

    print(f"AV  -> Cap 70ans: {capital_at_70_av:,.0f}")
    print(f"AV  -> Total Net Retraits: {total_net_withdrawals_av:,.0f}")
    print(f"AV  -> Cap Final Décès: {capital_at_80_av:,.0f}")
    print(f"AV  -> PS Succ: {ps_succ:,.0f} | Tax Succ: {tax_av:,.0f}")
    print(f"AV  -> NET HEIR: {net_heir_av:,.0f}")
    print(f"TOTAL VALUE (Heir + Withdrawals): {net_heir_av + total_net_withdrawals_av:,.0f}")

    print("\n=== SCENARIO 2: ACCIDENT (Forced Sale at 20y) ===")
    # 200k init, 30 ans de durée totale. Accident à l'année 20.
    cap_ini = 200_000
    yield_val = 0.08  # Rendement élevé pour accentuer l'effet fiscal
    fees_av = 0.005
    duration = 30
    accident_year = 20

    # --- CTO normal (sans accident) ---
    sim = SimulationEngine(cap_ini, yield_val, 0, envelope_type="CTO")
    for _ in range(duration):
        sim.advance_one_year()
    # Succession
    tax = calculate_succession_tax_marginal(sim.capital, 300_000)
    notary_fees_cto = calcul_emoluments_notaire(sim.capital)
    net_normal = sim.capital - tax - notary_fees_cto

    # --- CTO accident ---
    sim_acc = SimulationEngine(cap_ini, yield_val, 0, envelope_type="CTO")
    for y in range(duration):
        if y == accident_year:
            sim_acc.force_liquidation_tax_event("CTO")
        sim_acc.advance_one_year()
    # Succession
    # La purge efface l'impôt sur les gains.
    # Le coût vient du capital perdu en impôt à l'année 20 qui ne capitalise plus.
    tax_acc = calculate_succession_tax_marginal(sim_acc.capital, 300_000)
    notary_fees_acc = calcul_emoluments_notaire(sim_acc.capital)
    net_acc = sim_acc.capital - tax_acc - notary_fees_acc

    # --- AV (accident neutre) ---
    sim_av = SimulationEngine(cap_ini, yield_val, fees_av, envelope_type="AV")
    for y in range(duration):
        if y == accident_year:
            sim_av.force_liquidation_tax_event("AV")  # Sans effet
        sim_av.advance_one_year()
    gains = max(0, sim_av.capital - sim_av.total_versements)
    ps = gains * PS_RATE_AV
    base = max(0, sim_av.capital - ps - ABATTEMENT_AV_AVANT_70)
    tax_av = base * BAREME_AV_AVANT_70[0][1]  # Barème 990I
    net_av = sim_av.capital - ps - tax_av

    print(f"Yield: {yield_val*100}%")
    print(f"CTO Standard Net: {net_normal:,.0f}")
    print(f"CTO Accident Net: {net_acc:,.0f}")
    print(f"Perte due à l'accident CTO: {net_normal - net_acc:,.0f}")
    print(f"AV Net: {net_av:,.0f}")


if __name__ == "__main__":
    run_scenarios()
