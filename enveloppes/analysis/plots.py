import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

from ..core.constants import (
    ABATTEMENT_AV_AVANT_70,
    BAREME_AV_AVANT_70,
    ABATTEMENT_AV_APRES_70_GLOBAL,
)
from ..core.fiscalite import calcul_impot_progressif, get_regime_successoral
from ..succession.heritage import calculer_heritage_assurance_vie, calculer_heritage_cto

plt.rcParams.update({
    "font.size": 14,
    "axes.titlesize": 16,
    "axes.labelsize": 18,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 14,
    "figure.titlesize": 20,
})


def simuler_et_tracer(
    titre_prefix,
    capital_initial=100_000,
    autres_biens_valeur=300_000,
    nb_heriters=1,
    nb_beneficiaires=1,
    lien="ligne_directe",
    versements_av_avant70=True,
    frais_sociaux_av=0.172,
    duree_max=40,
    frais_av_max=0.02,
    rendement_max=0.10,
    frais_av_fixe=0.005,
    rendement_fixe=0.045,
    resolution=200,
    relatif=True,
    clip_range=None,
):
    if versements_av_avant70:
        abattement_av_par_benef = ABATTEMENT_AV_AVANT_70
        bareme_av = BAREME_AV_AVANT_70
    else:
        abattement_av_par_benef = ABATTEMENT_AV_APRES_70_GLOBAL / max(1, nb_beneficiaires)
        bareme_av = [(np.inf, 0.0)]

    abattement_fiscal_av_total = abattement_av_par_benef * nb_beneficiaires

    abattement_par_heritier, bareme_succession = get_regime_successoral(lien)
    abattement_succession_total = abattement_par_heritier * nb_heriters

    annees = np.linspace(0, duree_max, resolution)
    frais_gestion = np.linspace(0, frais_av_max, resolution)
    rendements = np.linspace(0, rendement_max, resolution)

    diff_heritage1 = np.zeros((resolution, resolution))
    for i in range(resolution):
        for j in range(resolution):
            av_result = calculer_heritage_assurance_vie(
                capital_initial,
                annees[j],
                rendement_fixe,
                frais_gestion[i],
                frais_sociaux_av,
                abattement_fiscal_av_total,
                bareme_av,
                versement_apres_70=(not versements_av_avant70),
            )

            impot_succession_marginal_av = 0.0
            if av_result.montant_soumis_succession > 0:
                base_autres = max(0.0, autres_biens_valeur - abattement_succession_total)
                droits_autres = calcul_impot_progressif(base_autres, bareme_succession)

                base_totale_av = max(
                    0.0,
                    autres_biens_valeur + av_result.montant_soumis_succession - abattement_succession_total,
                )
                droits_totaux_av_scenario = calcul_impot_progressif(base_totale_av, bareme_succession)
                impot_succession_marginal_av = droits_totaux_av_scenario - droits_autres

            av_net_real = av_result.heritage_net - impot_succession_marginal_av
            cto_result = calculer_heritage_cto(
                capital_initial,
                annees[j],
                rendement_fixe,
                autres_biens_valeur,
                abattement_succession_total,
                bareme_succession,
            )
            base_totale = cto_result.capital_final + autres_biens_valeur
            if relatif:
                diff_heritage1[i, j] = 0.0 if base_totale <= 0 else (
                    av_net_real - cto_result.heritage_net
                ) / base_totale
            else:
                diff_heritage1[i, j] = av_net_real - cto_result.heritage_net

    diff_heritage2 = np.zeros((resolution, resolution))
    for i in range(resolution):
        for j in range(resolution):
            av_result = calculer_heritage_assurance_vie(
                capital_initial,
                annees[j],
                rendements[i],
                frais_av_fixe,
                frais_sociaux_av,
                abattement_fiscal_av_total,
                bareme_av,
                versement_apres_70=(not versements_av_avant70),
            )

            impot_succession_marginal_av = 0.0
            if av_result.montant_soumis_succession > 0:
                base_autres = max(0.0, autres_biens_valeur - abattement_succession_total)
                droits_autres = calcul_impot_progressif(base_autres, bareme_succession)
                base_totale_av = max(
                    0.0,
                    autres_biens_valeur + av_result.montant_soumis_succession - abattement_succession_total,
                )
                droits_totaux_av_scenario = calcul_impot_progressif(base_totale_av, bareme_succession)
                impot_succession_marginal_av = droits_totaux_av_scenario - droits_autres

            av_net_real = av_result.heritage_net - impot_succession_marginal_av
            cto_result = calculer_heritage_cto(
                capital_initial,
                annees[j],
                rendements[i],
                autres_biens_valeur,
                abattement_succession_total,
                bareme_succession,
            )
            base_totale = cto_result.capital_final + autres_biens_valeur
            if relatif:
                diff_heritage2[i, j] = 0.0 if base_totale <= 0 else (
                    av_net_real - cto_result.heritage_net
                ) / base_totale
            else:
                diff_heritage2[i, j] = av_net_real - cto_result.heritage_net

    vmin = float(np.nanmin([diff_heritage1, diff_heritage2]))
    vmax = float(np.nanmax([diff_heritage1, diff_heritage2]))

    if clip_range is not None:
        vmin = max(vmin, clip_range[0])
        vmax = min(vmax, clip_range[1])

    cayas_colors = [
        "#7cfa72",
        "#75fafc",
        "#4451ff",
        "#6945d8",
        "#c5b5f8",
        "#ed1a79",
        "#ed81aa",
        "#ef9755",
        "#fcd414",
        "#FD5144",
    ]
    cmap_cayas = LinearSegmentedColormap.from_list("cayas", cayas_colors, N=256)

    fig_2d, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

    vmin = float(np.nanmin([diff_heritage1, diff_heritage2]))
    vmax = float(np.nanmax([diff_heritage1, diff_heritage2]))
    norm = TwoSlopeNorm(vmin=vmin, vcenter=0.0, vmax=vmax)

    im1 = ax1.imshow(
        diff_heritage1,
        origin="lower",
        extent=[0, duree_max, 0, frais_av_max],
        aspect="auto",
        norm=norm,
        cmap="RdYlBu",
    )
    ax1.set_title(f"Impact des frais (r fixe : {rendement_fixe*100}%/an)")
    ax1.set_xlabel("Années de placement")
    ax1.set_ylabel("Frais de gestion AV (%)")

    im2 = ax2.imshow(
        diff_heritage2,
        origin="lower",
        extent=[0, duree_max, 0, rendement_max],
        aspect="auto",
        norm=norm,
        cmap="RdYlBu",
    )
    ax2.set_title(f"Impact du rendement (frais fixes : {frais_av_fixe*100}%/an)")
    ax2.set_xlabel("Annees de placement")
    ax2.set_ylabel("Rendement annuel (%)")

    cbar_ax = fig_2d.add_axes([0.9, 0.15, 0.02, 0.7])
    cbar = fig_2d.colorbar(im1, cax=cbar_ax)
    cbar.set_label("Différence relative d'héritage net\n(AV - CTO) / (CTO + autres biens)")

    plt.tight_layout(rect=[0, 0, 0.9, 1])
    plt.show()


if __name__ == "__main__":
    capital_initial = 100_000
    autres_biens_1 = 300_000
    autres_biens_2 = 300_000

    simuler_et_tracer(
        titre_prefix="(enfants/parents)",
        capital_initial=capital_initial,
        autres_biens_valeur=autres_biens_2,
        nb_heriters=2,
        nb_beneficiaires=2,
        lien="ligne_directe",
        versements_av_avant70=True,
        duree_max=40,
    )

    simuler_et_tracer(
        titre_prefix="(enfants/parents)",
        capital_initial=capital_initial,
        autres_biens_valeur=autres_biens_1,
        nb_heriters=1,
        nb_beneficiaires=1,
        lien="ligne_directe",
        versements_av_avant70=True,
        duree_max=40,
    )

    simuler_et_tracer(
        titre_prefix="(neveu/nièce 55%)",
        capital_initial=capital_initial,
        autres_biens_valeur=autres_biens_1,
        nb_heriters=1,
        nb_beneficiaires=1,
        lien="neveu_niece",
        versements_av_avant70=True,
        duree_max=40,
    )

    simuler_et_tracer(
        titre_prefix="(frère/soeur 35%)",
        capital_initial=capital_initial,
        autres_biens_valeur=autres_biens_1,
        nb_heriters=1,
        nb_beneficiaires=1,
        lien="frere_soeur",
        versements_av_avant70=True,
        duree_max=40,
    )
