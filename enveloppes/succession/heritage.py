from ..core.fiscalite import calcul_emoluments_notaire, calcul_impot_progressif
from ..core.results import AssuranceVieResult, CTOResult


def calculer_heritage_assurance_vie(
    capital_initial,
    annee,
    rendement,
    frais_gestion,
    frais_sociaux,
    abattement_fiscal_av_total,
    bareme_av,
    versement_apres_70: bool = False,
) -> AssuranceVieResult:
    """Calcule les montants nets et l'impot applique au contrat d'assurance-vie."""
    rendement_net = rendement - frais_gestion
    capital_final = capital_initial * (1 + rendement_net) ** annee
    plus_value = capital_final - capital_initial

    prelevements_sociaux = max(0.0, plus_value) * frais_sociaux
    capital_apres_ps = capital_final - prelevements_sociaux

    base_imposable_av = max(0.0, capital_apres_ps - abattement_fiscal_av_total)
    droits_av = calcul_impot_progressif(base_imposable_av, bareme_av)

    heritage_net = capital_apres_ps - droits_av

    montant_soumis_succession = 0.0
    if versement_apres_70:
        montant_soumis_succession = max(0.0, capital_initial - abattement_fiscal_av_total)

    return AssuranceVieResult(
        heritage_net=heritage_net,
        capital_final=capital_final,
        prelevements_sociaux=prelevements_sociaux,
        droits_av=droits_av,
        montant_soumis_succession=montant_soumis_succession,
    )


def calculer_heritage_cto(
    capital_initial,
    annee,
    rendement,
    autres_biens_valeur,
    abattement_succession_total,
    bareme_succession,
) -> CTOResult:
    """Calcule les montants nets et l'impot impute au CTO lors de la succession."""
    capital_final_cto = capital_initial * (1 + rendement) ** annee

    actif_total = capital_final_cto + avec_autres_biens(autres_biens_valeur)
    base_imposable_totale = max(0.0, actif_total - abattement_succession_total)

    droits_totaux = calcul_impot_progressif(base_imposable_totale, bareme_succession)

    part_cto = 0.0 if actif_total == 0 else capital_final_cto / actif_total
    droits_imputes_cto = droits_totaux * part_cto

    notary_fees = calcul_emoluments_notaire(capital_final_cto)
    heritage_net = capital_final_cto - droits_imputes_cto - notary_fees
    return CTOResult(
        heritage_net=heritage_net,
        capital_final=capital_final_cto,
        droits_imputes_cto=droits_imputes_cto,
        droits_totaux=droits_totaux,
    )


def avec_autres_biens(valeur):
    """Aide pour la lisibilite."""
    return valeur


def calculer_heritage_cto_iteratif(
    capital_initial,
    annee,
    rendement,
    autres_biens_valeur,
    abattement_succession_total,
    bareme_succession,
    taux_rotation=0.0,
    flat_tax=0.312,
) -> CTOResult:
    """
    Simule la croissance d'un CTO annee par annee avec un taux de rotation.
    taux_rotation: fraction du capital vendue et rachetee chaque annee.
    flat_tax: impot sur les plus-values realisees (30%).
    """
    valeur_actuelle = capital_initial
    pru_actuel = capital_initial

    for _ in range(int(annee)):
        valeur_avant_rotation = valeur_actuelle * (1 + rendement)

        valeur_vendue = valeur_avant_rotation * taux_rotation
        pru_vendu = pru_actuel * taux_rotation

        pv_realisee = max(0.0, valeur_vendue - pru_vendu)
        impot_rotation = pv_realisee * flat_tax

        valeur_actuelle = valeur_avant_rotation - impot_rotation

        pru_actuel = pru_actuel * (1 - taux_rotation) + (valeur_vendue - impot_rotation)

    actif_total = valeur_actuelle + autres_biens_valeur
    base_imposable_totale = max(0.0, actif_total - abattement_succession_total)
    droits_totaux = calcul_impot_progressif(base_imposable_totale, bareme_succession)

    part_cto = 0.0 if actif_total == 0 else valeur_actuelle / actif_total
    droits_imputes_cto = droits_totaux * part_cto
    notary_fees = calcul_emoluments_notaire(valeur_actuelle)
    heritage_net = valeur_actuelle - droits_imputes_cto - notary_fees

    return CTOResult(
        heritage_net=heritage_net,
        capital_final=valeur_actuelle,
        droits_imputes_cto=droits_imputes_cto,
        droits_totaux=droits_totaux,
    )
