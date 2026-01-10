import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

from enveloppes.core.constants import (
    ABATTEMENT_AV_ANNUEL_INDIVIDUEL,
    ABATTEMENT_AV_AVANT_70,
    BAREME_AV_AVANT_70,
    PS_RATE_AV,
)
from enveloppes.core.fiscalite import (
    calcul_emoluments_notaire,
    calculate_succession_tax_marginal,
)
from enveloppes.envelopes.av import AVSimulation
from enveloppes.envelopes.cto import CTOSimulation


def run_rente_senior_heatmap():
    print("Génération de la heatmap rente senior (rendement vs âge au décès)...")

    # Plages
    death_ages = np.arange(76, 101)  # 76 à 100
    resol_y = len(death_ages)

    resol_x = 200
    yields = np.linspace(0.02, 0.10, resol_x)

    # Paramètres fixes
    cap_ini = 100_000
    start_age = 65
    retire_age = 75
    withdrawal_net = 3000
    fees_av = 0.005
    autres_biens = 300_000

    z = np.zeros((resol_y, resol_x))

    for i, death_age in enumerate(death_ages):  # Axe Y
        for j, yld in enumerate(yields):  # Axe X
            accum_duration = int(retire_age - start_age)
            withdrawal_duration = int(death_age - retire_age)

            # --- CTO ---
            sim_cto = CTOSimulation(cap_ini, yld)
            for _ in range(accum_duration):
                sim_cto.advance_one_year()

            net_withdrawals_cto = 0
            for _ in range(withdrawal_duration):
                net_withdrawals_cto += sim_cto.withdraw_net(withdrawal_net)
                sim_cto.advance_one_year()

            tax_cto = calculate_succession_tax_marginal(sim_cto.capital, autres_biens)
            notary_fees_cto = calcul_emoluments_notaire(sim_cto.capital)
            net_heir_cto = sim_cto.capital - tax_cto - notary_fees_cto
            total_cto = net_withdrawals_cto + net_heir_cto

            # --- AV ---
            sim_av = AVSimulation(cap_ini, yld, frais_gestion_av=fees_av)
            for _ in range(accum_duration):
                sim_av.advance_one_year()

            net_withdrawals_av = 0
            for _ in range(withdrawal_duration):
                net_withdrawals_av += sim_av.withdraw_net(
                    withdrawal_net,
                    abattement_av_annuel=ABATTEMENT_AV_ANNUEL_INDIVIDUEL,
                )
                sim_av.advance_one_year()

            # Succession
            gains_succ = max(0, sim_av.capital - sim_av.total_versements)
            ps_succ = gains_succ * PS_RATE_AV
            base_taxable_av = max(0, sim_av.capital - ps_succ - ABATTEMENT_AV_AVANT_70)
            tax_av = 0.0
            if base_taxable_av > 0:
                tax_av = base_taxable_av * BAREME_AV_AVANT_70[0][1]
            net_heir_av = sim_av.capital - ps_succ - tax_av
            total_av = net_withdrawals_av + net_heir_av
            
            # Net des autres biens
            tax_autres_only = calculate_succession_tax_marginal(0, autres_biens)
            net_autres = autres_biens - tax_autres_only

            total_av_global = total_av + net_autres
            total_cto_global = total_cto + net_autres

            # Comparaison
            max_global = max(total_av_global, total_cto_global)

            if max_global > 0:
                z[i, j] = (total_av_global - total_cto_global) / max_global * 100.0
            else:
                z[i, j] = 0.0

    plt.figure(figsize=(12, 10))
    norm = TwoSlopeNorm(vmin=min(np.min(z), -2), vcenter=0, vmax=max(np.max(z), 2))

    plt.imshow(
        z,
        origin="lower",
        extent=[yields[0] * 100, yields[-1] * 100, death_ages[0], death_ages[-1]],
        aspect="auto",
        cmap="RdYlGn",
        norm=norm,
        interpolation="bicubic",
    )

    plt.colorbar(label="Avantage relatif (%) : vert = AV, rouge = CTO")
    plt.xlabel("Rendement annuel (%)")
    plt.ylabel("Âge au décès (début rente à 75 ans)")
    plt.title("Scénario rente senior : CTO vs AV (capital 100k, retrait 3k€ net/an)")

    plt.contour(yields * 100, death_ages, z, levels=[0], colors="black", linestyles="dashed")

    output_path = os.path.join(os.path.dirname(__file__), "../images/heatmap_rente_senior.png")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Enregistré : {output_path}")

if __name__ == "__main__":
    run_rente_senior_heatmap()
