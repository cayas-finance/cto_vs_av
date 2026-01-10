import numpy as np

from ..core.fiscalite import calcul_emoluments_notaire, calcul_impot_progressif
from .heritage import avec_autres_biens


def calculer_heritage_stochastique(
    capital_initial,
    annee,
    rendement_espere,
    volatilite,
    frais_gestion_av,
    frais_sociaux_av,
    autres_biens_valeur,
    abattement_succession_total,
    bareme_succession,
    abattement_fiscal_av_total,
    bareme_av,
    taux_rotation=0.0,
    flat_tax=0.312,
    nb_trajectoires=1000,
    seed=None,
):
    """
    Simule nb_trajectoires avec un modele de mouvement brownien geometrique.
    Retourne un dictionnaire avec les distributions des heritages finaux.
    """
    if seed:
        np.random.seed(seed)

    dt = 1.0
    heritages_av = []
    heritages_cto = []
    total_av_nets = []
    total_cto_nets = []

    base_autres = max(0.0, autres_biens_valeur - abattement_succession_total)
    tax_autres_only = calcul_impot_progressif(base_autres, bareme_succession)
    net_autres = autres_biens_valeur - tax_autres_only

    mu = rendement_espere
    sigma = volatilite

    for _ in range(nb_trajectoires):
        val_av = capital_initial
        val_cto = capital_initial
        pru_cto = capital_initial

        for _t in range(int(annee)):
            z = np.random.normal()
            r_t = np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z) - 1

            val_av = val_av * (1 + r_t - frais_gestion_av)

            val_cto_avant = val_cto * (1 + r_t)
            val_vendue = val_cto_avant * taux_rotation
            pru_vendu = pru_cto * taux_rotation
            pv_realisee = max(0.0, val_vendue - pru_vendu)
            impot = pv_realisee * flat_tax
            val_cto = val_cto_avant - impot
            pru_cto = pru_cto * (1 - taux_rotation) + (val_vendue - impot)

        plus_value_av = max(0.0, val_av - capital_initial)
        ps_av = plus_value_av * frais_sociaux_av
        cap_av_apres_ps = val_av - ps_av
        droits_av = calcul_impot_progressif(
            max(0.0, cap_av_apres_ps - abattement_fiscal_av_total),
            bareme_av,
        )
        heritage_av = cap_av_apres_ps - droits_av
        heritages_av.append(heritage_av)
        total_av_nets.append(heritage_av + net_autres)

        actif_total_cto = val_cto + avec_autres_biens(autres_biens_valeur)
        base_imposable_cto = max(0.0, actif_total_cto - abattement_succession_total)
        droits_totaux_cto = calcul_impot_progressif(base_imposable_cto, bareme_succession)
        part_cto = val_cto / actif_total_cto if actif_total_cto > 0 else 0
        droits_imputes_cto = droits_totaux_cto * part_cto
        notary_fees = calcul_emoluments_notaire(val_cto)
        heritage_cto = val_cto - droits_imputes_cto - notary_fees
        heritages_cto.append(heritage_cto)
        total_cto_nets.append(val_cto + autres_biens_valeur - droits_totaux_cto - notary_fees)

    return {
        "av": np.array(heritages_av),
        "cto": np.array(heritages_cto),
        "av_total": np.array(total_av_nets),
        "cto_total": np.array(total_cto_nets),
    }
