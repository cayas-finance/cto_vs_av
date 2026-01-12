from enveloppes.core.constants import (
    ABATTEMENT_AV_AVANT_70,
    BAREME_AV_AVANT_70,
    FLAT_TAX_CTO,
    PS_RATE_AV,
)
from enveloppes.core.fiscalite import (
    calcul_emoluments_notaire,
    calcul_impot_progressif,
    calculate_succession_tax_marginal,
)


def simulate_distributing_asset(
    capital_initial,
    years,
    distribution_rate,
    growth_rate,
    tax_rate=0.0,
    fees_rate=0.0,
):
    capital = capital_initial
    total_taxes = 0.0
    total_fees = 0.0

    for _ in range(years):
        base = capital
        distribution = base * distribution_rate
        tax = distribution * tax_rate
        fees = base * fees_rate

        capital = base + (distribution - tax) + (base * growth_rate) - fees
        total_taxes += tax
        total_fees += fees

    return capital, total_taxes, total_fees


def run_scenario():
    capital_initial = 100_000
    years = 20
    distribution_rate = 0.05
    growth_rate = 0.01
    frais_av = 0.005
    autres_biens = 300_000

    cap_cto, taxes_dividendes, _ = simulate_distributing_asset(
        capital_initial,
        years,
        distribution_rate,
        growth_rate,
        tax_rate=FLAT_TAX_CTO,
    )
    tax_succ_cto = calculate_succession_tax_marginal(cap_cto, autres_biens, "ligne_directe")
    notary_fees_cto = calcul_emoluments_notaire(cap_cto)
    net_heir_cto = cap_cto - tax_succ_cto - notary_fees_cto

    cap_av, _, fees_av = simulate_distributing_asset(
        capital_initial,
        years,
        distribution_rate,
        growth_rate,
        fees_rate=frais_av,
    )
    gains_av = max(0.0, cap_av - capital_initial)
    ps_succ = gains_av * PS_RATE_AV
    base_taxable_av = max(0.0, cap_av - ps_succ - ABATTEMENT_AV_AVANT_70)
    tax_av = calcul_impot_progressif(base_taxable_av, BAREME_AV_AVANT_70)
    net_heir_av = cap_av - ps_succ - tax_av

    diff = net_heir_av - net_heir_cto
    diff_rel = 0.0
    if max(net_heir_av, net_heir_cto) > 0:
        diff_rel = diff / max(net_heir_av, net_heir_cto)

    print("=== SCENARIO ACTIF DISTRIBUANT (SCPI/DIVIDENDES) ===")
    print(
        "Hypotheses: cap 100k, distribution 5%, appreciation 1%, "
        "20 ans, AV 0.5% frais, autres biens 300k."
    )
    print(f"CTO -> Capital final brut: {cap_cto:,.0f}")
    print(f"CTO -> Impots dividendes cumulés: {taxes_dividendes:,.0f}")
    print(f"CTO -> Taxe succession: {tax_succ_cto:,.0f}")
    print(f"CTO -> Frais notaire: {notary_fees_cto:,.0f}")
    print(f"CTO -> Net héritier: {net_heir_cto:,.0f}")
    print("")
    print(f"AV  -> Capital final brut: {cap_av:,.0f}")
    print(f"AV  -> Frais de gestion cumulés: {fees_av:,.0f}")
    print(f"AV  -> Prélèvements sociaux: {ps_succ:,.0f}")
    print(f"AV  -> Taxe 990I: {tax_av:,.0f}")
    print(f"AV  -> Net héritier: {net_heir_av:,.0f}")
    print("")
    print(f"Avantage AV vs CTO: {diff:,.0f} ({diff_rel:+.2%})")


if __name__ == "__main__":
    run_scenario()
