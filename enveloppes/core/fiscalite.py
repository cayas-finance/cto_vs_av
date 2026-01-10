import numpy as np

from .constants import (
    ABATTEMENT_FRERE_SOEUR,
    ABATTEMENT_LIGNE_DIRECTE,
    ABATTEMENT_NEVEU_NIECE,
    ABATTEMENT_TIERS,
    BAREME_FRERE_SOEUR,
    BAREME_LIGNE_DIRECTE,
    BAREME_NEVEU_NIECE,
    BAREME_TIERS,
    NOTARY_EMOLUMENTS_DONATION_BAREME,
    NOTARY_EMOLUMENTS_VAT_RATE,
)


def calcul_impot_progressif(base_imposable, bareme):
    """
    Calcule un impot selon un bareme progressif.
    bareme: liste de tuples (plafond, taux) triee par plafonds croissants.
            Utiliser np.inf pour le dernier plafond.
    """
    if base_imposable <= 0:
        return 0.0
    impot = 0.0
    prev = 0.0
    for plafond, taux in bareme:
        tranche_haute = min(base_imposable, plafond)
        if tranche_haute > prev:
            impot += (tranche_haute - prev) * taux
            prev = tranche_haute
        if base_imposable <= plafond:
            break
    return impot


def calcul_emoluments_notaire(
    valeur,
    bareme=NOTARY_EMOLUMENTS_DONATION_BAREME,
    tva_rate=NOTARY_EMOLUMENTS_VAT_RATE,
):
    if valeur <= 0:
        return 0.0
    emoluments_ht = calcul_impot_progressif(valeur, bareme)
    return emoluments_ht * (1 + tva_rate)


def bareme_forfait(taux):
    """Bareme forfaitaire (tout a un taux unique)."""
    return [(np.inf, taux)]


def get_regime_successoral(lien: str):
    """
    Retourne (abattement_par_heritier, bareme) selon le 'lien' demande.
    Valeurs indicatives usuelles en France (a ajuster si necessaire).
    """
    lien = lien.lower()
    if lien in ("ligne_directe", "directe", "enfant", "parent-enfant"):
        abattement = ABATTEMENT_LIGNE_DIRECTE
        bareme = BAREME_LIGNE_DIRECTE
    elif lien in ("frere_soeur", "frère_soeur", "frere-soeur"):
        abattement = ABATTEMENT_FRERE_SOEUR
        bareme = BAREME_FRERE_SOEUR
    elif lien in ("neveu_niece", "neveu-niece", "neveu-nièce", "neveu", "nièce", "niece"):
        abattement = ABATTEMENT_NEVEU_NIECE
        bareme = BAREME_NEVEU_NIECE
    elif lien in ("sans_lien", "aucun_lien", "tiers"):
        abattement = ABATTEMENT_TIERS
        bareme = BAREME_TIERS
    else:
        raise ValueError(f"Lien non reconnu: {lien}")
    return abattement, bareme


def calculate_succession_tax_marginal(
    masse_taxable,
    autres_biens,
    regime_code="ligne_directe",
    nb_benef=1,
):
    abattement, bareme = get_regime_successoral(regime_code)

    base_autres_par_benef = max(0, (autres_biens / nb_benef) - abattement)
    tax_autres = calcul_impot_progressif(base_autres_par_benef, bareme) * nb_benef

    base_total_par_benef = max(0, ((autres_biens + masse_taxable) / nb_benef) - abattement)
    tax_total = calcul_impot_progressif(base_total_par_benef, bareme) * nb_benef

    return tax_total - tax_autres
