from dataclasses import dataclass

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from .constants import (
    ABATTEMENT_LIGNE_DIRECTE, BAREME_LIGNE_DIRECTE,
    ABATTEMENT_FRERE_SOEUR, BAREME_FRERE_SOEUR,
    ABATTEMENT_NEVEU_NIECE, BAREME_NEVEU_NIECE,
    ABATTEMENT_TIERS, BAREME_TIERS,
    ABATTEMENT_AV_AVANT_70, BAREME_AV_AVANT_70,
    ABATTEMENT_AV_APRES_70_GLOBAL,
    NOTARY_EMOLUMENTS_DONATION_BAREME, NOTARY_EMOLUMENTS_VAT_RATE
)

plt.rcParams.update({
    "font.size": 14,          # taille par défaut pour tout le texte
    "axes.titlesize": 16,     # titre des axes
    "axes.labelsize": 18,     # labels x/y
    "xtick.labelsize": 12,    # ticks en x
    "ytick.labelsize": 12,    # ticks en y
    "legend.fontsize": 14,    # légendes
    "figure.titlesize": 20    # titre de la figure
})


# ---------- Outil générique : barème progressif ----------
def calcul_impot_progressif(base_imposable, bareme):
    """
    Calcule un impôt selon un barème progressif.
    bareme: liste de tuples (plafond, taux) triée par plafonds croissants.
            Utiliser np.inf pour le dernier plafond.
    """
    if base_imposable <= 0:
        return 0.0
    impôt = 0.0
    prev = 0.0
    for plafond, taux in bareme:
        tranche_haute = min(base_imposable, plafond)
        if tranche_haute > prev:
            impôt += (tranche_haute - prev) * taux
            prev = tranche_haute
        if base_imposable <= plafond:
            break
    return impôt

def calcul_emoluments_notaire(valeur, bareme=NOTARY_EMOLUMENTS_DONATION_BAREME, tva_rate=NOTARY_EMOLUMENTS_VAT_RATE):
    if valeur <= 0:
        return 0.0
    emoluments_ht = calcul_impot_progressif(valeur, bareme)
    return emoluments_ht * (1 + tva_rate)

# ---------- Barèmes de succession par lien de parenté ----------
def bareme_forfait(taux):
    """Barème forfaitaire (tout à un taux unique)."""
    return [(np.inf, taux)]

def get_regime_successoral(lien: str):
    """
    Retourne (abattement_par_heritier, bareme) selon le 'lien' demandé.
    Valeurs indicatives usuelles en France (à ajuster si nécessaire).
    """
    lien = lien.lower()
    if lien in ("ligne_directe", "directe", "enfant", "parent-enfant"):
        # Enfants/parents (ligne directe)
        abattement = ABATTEMENT_LIGNE_DIRECTE
        bareme = BAREME_LIGNE_DIRECTE
    elif lien in ("frere_soeur", "frère_soeur", "frere-soeur"):
        # Frères / soeurs
        abattement = ABATTEMENT_FRERE_SOEUR
        bareme = BAREME_FRERE_SOEUR
    elif lien in ("neveu_niece", "neveu-nièce", "neveu", "nièce", "niece"):
        # Neveux / nièces
        abattement = ABATTEMENT_NEVEU_NIECE
        bareme = BAREME_NEVEU_NIECE
    elif lien in ("sans_lien", "aucun_lien", "tiers"):
        # Tiers (sans lien de parenté)
        abattement = ABATTEMENT_TIERS
        bareme = BAREME_TIERS
    else:
        raise ValueError(f"Lien non reconnu: {lien}")
    return abattement, bareme

@dataclass
class AssuranceVieResult:
    heritage_net: float
    capital_final: float
    prelevements_sociaux: float
    droits_av: float
    montant_soumis_succession: float = 0.0


@dataclass
class CTOResult:
    heritage_net: float
    capital_final: float
    droits_imputes_cto: float
    droits_totaux: float


# ---------- Assurance-vie ----------
def calculer_heritage_assurance_vie(
    capital_initial, annee, rendement, frais_gestion, frais_sociaux,
    abattement_fiscal_av_total, bareme_av,
    versement_apres_70: bool = False
) -> AssuranceVieResult:
    """Calcule les montants nets et l'impôt appliqués au contrat d'assurance-vie."""
    rendement_net = rendement - frais_gestion
    capital_final = capital_initial * (1 + rendement_net) ** annee
    plus_value = capital_final - capital_initial

    # Prélèvements sociaux sur plus-values (jamais négatifs)
    prelevements_sociaux = max(0.0, plus_value) * frais_sociaux
    capital_apres_ps = capital_final - prelevements_sociaux

    # Fiscalité spécifique AV après abattement AV
    base_imposable_av = max(0.0, capital_apres_ps - abattement_fiscal_av_total)
    droits_av = calcul_impot_progressif(base_imposable_av, bareme_av)

    heritage_net = capital_apres_ps - droits_av
    heritage_net = capital_apres_ps - droits_av
    
    montant_soumis_succession = 0.0
    if versement_apres_70:
        # Régime 757B : les primes versées (capital_initial) moins l'abattement (30 500 total)
        # sont soumises aux droits de succession.
        # Attention, l'abattement de 30 500 est global. Ici on suppose que 'abattement_fiscal_av_total'
        # contient la part d'abattement allouée à ce contrat/bénéficiaire.
        # Si c'est le seul contrat, c'est 30 500.
        montant_soumis_succession = max(0.0, capital_initial - abattement_fiscal_av_total)

    return AssuranceVieResult(
        heritage_net=heritage_net,
        capital_final=capital_final,
        prelevements_sociaux=prelevements_sociaux,
        droits_av=droits_av,
        montant_soumis_succession=montant_soumis_succession
    )


# ---------- CTO / Succession ----------
def calculer_heritage_cto(
    capital_initial, annee, rendement,
    autres_biens_valeur,
    abattement_succession_total,
    bareme_succession
) -> CTOResult:
    """Calcule les montants nets et l'impôt imputé au CTO lors de la succession."""
    capital_final_cto = capital_initial * (1 + rendement) ** annee

    actif_total = capital_final_cto + avec_autres_biens(autres_biens_valeur)
    base_imposable_totale = max(0.0, actif_total - abattement_succession_total)

    droits_totaux = calcul_impot_progressif(base_imposable_totale, bareme_succession)

    # Imputation proportionnelle de l'impôt au CTO
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
    """Aide pour la lisibilité."""
    return valeur

def calculer_heritage_cto_iteratif(
    capital_initial, annee, rendement,
    autres_biens_valeur,
    abattement_succession_total,
    bareme_succession,
    taux_rotation=0.0,
    flat_tax=0.312
) -> CTOResult:
    """
    Simule la croissance d'un CTO année par année avec un taux de rotation (rééquilibrage).
    taux_rotation: fraction du capital vendue et rachetée chaque année.
    flat_tax: impôt sur les plus-values réalisées (30%).
    """
    valeur_actuelle = capital_initial
    pru_actuel = capital_initial # Prix de revient unitaire (assiette fiscale)
    
    for _ in range(int(annee)):
        # 1. Croissance annuelle
        valeur_avant_rotation = valeur_actuelle * (1 + rendement)
        
        # 2. Rotation (rééquilibrage)
        # On vend une fraction 'taux_rotation' de la valeur actuelle
        valeur_vendue = valeur_avant_rotation * taux_rotation
        pru_vendu = pru_actuel * taux_rotation
        
        # Plus-value sur la partie vendue
        pv_realisee = max(0.0, valeur_vendue - pru_vendu)
        impot_rotation = pv_realisee * flat_tax
        
        # Mise à jour de la valeur (on déduit l'impôt)
        valeur_actuelle = valeur_avant_rotation - impot_rotation
        
        # Mise à jour du PRU
        # Le PRU de la partie non vendue reste le même.
        # Le PRU de la partie rachetée est (valeur_vendue - impot_rotation)
        pru_actuel = pru_actuel * (1 - taux_rotation) + (valeur_vendue - impot_rotation)

    # Succession finale
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

def calculer_heritage_stochastique(
    capital_initial, annee, rendement_espere, volatilite,
    frais_gestion_av, frais_sociaux_av,
    autres_biens_valeur, abattement_succession_total, bareme_succession,
    abattement_fiscal_av_total, bareme_av,
    taux_rotation=0.0, flat_tax=0.312, nb_trajectoires=1000, seed=None
):
    """
    Simule nb_trajectoires avec un modèle de mouvement brownien géométrique.
    Retourne un dictionnaire avec les distributions des heritages finaux.
    """
    if seed: np.random.seed(seed)
    
    dt = 1.0 # Pas de temps annuel
    heritages_av = []
    heritages_cto = []
    total_av_nets = []
    total_cto_nets = []

    base_autres = max(0.0, autres_biens_valeur - abattement_succession_total)
    tax_autres_only = calcul_impot_progressif(base_autres, bareme_succession)
    net_autres = autres_biens_valeur - tax_autres_only
    
    # Prégénérer les rendements (log-normaux)
    # r = exp((mu - 0.5*sigma^2)dt + sigma*sqrt(dt)*Z)
    mu = rendement_espere
    sigma = volatilite
    
    for _ in range(nb_trajectoires):
        # 1. Simulation AV (Déterministe par rapport aux rendements réalisés)
        # 2. Simulation CTO (Itérative pour la rotation)
        
        val_av = capital_initial
        val_cto = capital_initial
        pru_cto = capital_initial
        
        for _t in range(int(annee)):
            # Rendement aléatoire de l'année
            z = np.random.normal()
            r_t = np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z) - 1
            
            # --- AV ---
            val_av = val_av * (1 + r_t - frais_gestion_av)
            
            # --- CTO ---
            val_cto_avant = val_cto * (1 + r_t)
            # Rotation
            val_vendue = val_cto_avant * taux_rotation
            pru_vendu = pru_cto * taux_rotation
            pv_realisee = max(0.0, val_vendue - pru_vendu)
            impot = pv_realisee * flat_tax
            val_cto = val_cto_avant - impot
            pru_cto = pru_cto * (1 - taux_rotation) + (val_vendue - impot)
            
        # Fin de simulation : Succession
        # AV
        plus_value_av = max(0.0, val_av - capital_initial) # Simplification: base = capital_initial
        ps_av = plus_value_av * frais_sociaux_av
        cap_av_apres_ps = val_av - ps_av
        droits_av = calcul_impot_progressif(max(0.0, cap_av_apres_ps - abattement_fiscal_av_total), bareme_av)
        heritage_av = cap_av_apres_ps - droits_av
        heritages_av.append(heritage_av)
        total_av_nets.append(heritage_av + net_autres)
        
        # CTO (Purge des PV latentes)
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

# ---------- Simulation + tracé ----------
from matplotlib.colors import TwoSlopeNorm

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
    relatif=True,               # <<--- NEW : différence relative si True
    clip_range=None             # ex: (-0.5, 0.5) pour clipper la palette
):
    # Barème AV
    if versements_av_avant70:
        abattement_av_par_benef = ABATTEMENT_AV_AVANT_70
        bareme_av = BAREME_AV_AVANT_70
    else:
        # Régime 757 B (> 70 ans)
        # L'abattement de 30 500 est global (tous bénéficiaires).
        # L'allocation s'applique par bénéficiaire simulé ; un seul bénéficiaire utilise le montant complet.
        abattement_av_par_benef = ABATTEMENT_AV_APRES_70_GLOBAL / max(1, nb_beneficiaires)
        
        # Pour le calcul des droits SPECIFIQUES AV (990 I), le barème est 0% car ce n'est pas ce prélèvement qui s'applique.
        bareme_av = [(np.inf, 0.0)]

    abattement_fiscal_av_total = abattement_av_par_benef * nb_beneficiaires

    # Succession selon le lien
    abattement_par_heritier, bareme_succession = get_regime_successoral(lien)
    abattement_succession_total = abattement_par_heritier * nb_heriters

    # Grilles
    annees = np.linspace(0, duree_max, resolution)
    frais_gestion = np.linspace(0, frais_av_max, resolution)
    rendements = np.linspace(0, rendement_max, resolution)

    # --- Heatmap Frais vs Durée (r fixe) ---
    diff_heritage1 = np.zeros((resolution, resolution))
    for i in range(resolution):
        for j in range(resolution):
            av_result = calculer_heritage_assurance_vie(
                capital_initial, annees[j], rendement_fixe, frais_gestion[i], frais_sociaux_av,
                abattement_fiscal_av_total, bareme_av,
                versement_apres_70=(not versements_av_avant70)
            )
            
            # Correction succession AV > 70 ans :
            # Si montant_soumis_succession > 0, il faut calculer l'impôt de succession marginal qu'il génère
            # en s'ajoutant aux "autres biens".
            impot_succession_marginal_av = 0.0
            if av_result.montant_soumis_succession > 0:
                # 1. Droits sur les autres biens seuls
                base_autres = max(0.0, autres_biens_valeur - abattement_succession_total)
                droits_autres = calcul_impot_progressif(base_autres, bareme_succession)
                
                # 2. Droits sur (autres biens + part taxable AV)
                base_totale_av = max(0.0, autres_biens_valeur + av_result.montant_soumis_succession - abattement_succession_total)
                droits_totaux_av_scenario = calcul_impot_progressif(base_totale_av, bareme_succession)
                
                # 3. Impôt imputable à l'AV
                impot_succession_marginal_av = droits_totaux_av_scenario - droits_autres
            
            av_net_real = av_result.heritage_net - impot_succession_marginal_av
            cto_result = calculer_heritage_cto(
                capital_initial, annees[j], rendement_fixe,
                autres_biens_valeur,
                abattement_succession_total,
                bareme_succession
            )
            base_totale = cto_result.capital_final + autres_biens_valeur
            if relatif:
                # éviter /0 : si base_totale=0 on met 0 (ou np.nan si tu préfères)
                diff_heritage1[i, j] = 0.0 if base_totale <= 0 else (av_net_real - cto_result.heritage_net) / base_totale
            else:
                diff_heritage1[i, j] = av_net_real - cto_result.heritage_net

    # --- Heatmap Rendement vs Durée (frais fixes) ---
    diff_heritage2 = np.zeros((resolution, resolution))
    for i in range(resolution):
        for j in range(resolution):
            av_result = calculer_heritage_assurance_vie(
                capital_initial, annees[j], rendements[i], frais_av_fixe, frais_sociaux_av,
                abattement_fiscal_av_total, bareme_av,
                versement_apres_70=(not versements_av_avant70)
            )
            
            impot_succession_marginal_av = 0.0
            if av_result.montant_soumis_succession > 0:
                base_autres = max(0.0, autres_biens_valeur - abattement_succession_total)
                droits_autres = calcul_impot_progressif(base_autres, bareme_succession)
                base_totale_av = max(0.0, autres_biens_valeur + av_result.montant_soumis_succession - abattement_succession_total)
                droits_totaux_av_scenario = calcul_impot_progressif(base_totale_av, bareme_succession)
                impot_succession_marginal_av = droits_totaux_av_scenario - droits_autres

            av_net_real = av_result.heritage_net - impot_succession_marginal_av
            cto_result = calculer_heritage_cto(
                capital_initial, annees[j], rendements[i],
                autres_biens_valeur,
                abattement_succession_total,
                bareme_succession
            )
            base_totale = cto_result.capital_final + autres_biens_valeur
            if relatif:
                diff_heritage2[i, j] = 0.0 if base_totale <= 0 else (av_net_real - cto_result.heritage_net) / base_totale
            else:
                diff_heritage2[i, j] = av_net_real - cto_result.heritage_net

    # --- Harmonisation de l'échelle & tracé ---
    # bornes communes (ignorer d'éventuels NaN)
    vmin = float(np.nanmin([diff_heritage1, diff_heritage2]))
    vmax = float(np.nanmax([diff_heritage1, diff_heritage2]))

    # optionnel : clipper pour éviter une palette écrasée par quelques valeurs extrêmes
    if clip_range is not None:
        vmin = max(vmin, clip_range[0])
        vmax = min(vmax, clip_range[1])


    # --- Palette Cayas ---
    cayas_colors = [
        "#7cfa72",  # Flash green
        "#75fafc",  # Neon blue
        "#4451ff",  # Royal blue
        "#6945d8",  # Electric purple
        "#c5b5f8",  # Lilac
        "#ed1a79",  # Fushia
        "#ed81aa",  # Pink
        "#ef9755",  # Orange
        "#fcd414",  # Yellow
        "#FD5144"  # Red
    ]
    cmap_cayas = LinearSegmentedColormap.from_list("cayas", cayas_colors, N=256)

    # --- Figure ---
    fig_2d, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

    # bornes communes
    vmin = float(np.nanmin([diff_heritage1, diff_heritage2]))
    vmax = float(np.nanmax([diff_heritage1, diff_heritage2]))
    norm = TwoSlopeNorm(vmin=vmin, vcenter=0.0, vmax=vmax)

    # tracés
    im1 = ax1.imshow(diff_heritage1, origin="lower",
                     extent=[0, duree_max, 0, frais_av_max], aspect="auto",
                     norm=norm, cmap="RdYlBu")
    ax1.set_title(f"Impact des frais (r fixe : {rendement_fixe*100}%/an)")
    ax1.set_xlabel("Années de placement")
    ax1.set_ylabel("Frais de gestion AV (%)")

    im2 = ax2.imshow(diff_heritage2, origin="lower",
                     extent=[0, duree_max, 0, rendement_max], aspect="auto",
                     norm=norm, cmap="RdYlBu")
    ax2.set_title(f"Impact du rendement (frais fixes : {frais_av_fixe*100}%/an)")
    ax2.set_xlabel("Années de placement")
    ax2.set_ylabel("Rendement annuel (%)")

    # --- Axe pour la colorbar, placé à droite de la figure ---
    # [x0, y0, largeur, hauteur] en coordonnées figure (0–1)
    cbar_ax = fig_2d.add_axes([0.9, 0.15, 0.02, 0.7])
    cbar = fig_2d.colorbar(im1, cax=cbar_ax)
    cbar.set_label("Différence relative d'héritage net\n(AV - CTO) / (CTO + autres biens)")

    plt.tight_layout(rect=[0, 0, 0.9, 1])  # laisse de la place à droite pour la colorbar
    plt.show()


# ----------------- EXEMPLES D’USAGE -----------------
if __name__ == "__main__":
    # Hypothèses de base
    capital_initial = 100_000
    autres_biens_1 = 300_000
    autres_biens_2 = 300_000

    # Cas A — LIGNE DIRECTE
    simuler_et_tracer(
        titre_prefix="(enfants/parents)",
        capital_initial=capital_initial,
        autres_biens_valeur=autres_biens_2,   # ou autres_biens_2
        nb_heriters=2,
        nb_beneficiaires=2,
        lien="ligne_directe",
        versements_av_avant70=True,           # ici, 69 ans -> avant 70
        duree_max=40
    )

    simuler_et_tracer(
        titre_prefix="(enfants/parents)",
        capital_initial=capital_initial,
        autres_biens_valeur=autres_biens_1,  # ou autres_biens_2
        nb_heriters=1,
        nb_beneficiaires=1,
        lien="ligne_directe",
        versements_av_avant70=True,  # ici, 69 ans -> avant 70
        duree_max=40
    )

    # Cas B — LIGNE INDIRECTE (neveu/nièce à 55 %)
    simuler_et_tracer(
        titre_prefix="(neveu/nièce 55%)",
        capital_initial=capital_initial,
        autres_biens_valeur=autres_biens_1,   # ou autres_biens_2
        nb_heriters=1,
        nb_beneficiaires=1,
        lien="neveu_niece",
        versements_av_avant70=True,
        duree_max=40,
        frais_av_fixe=0.02,
    )

    simuler_et_tracer(
        titre_prefix="(neveu/nièce 55%)",
        capital_initial=capital_initial,
        autres_biens_valeur=autres_biens_1,  # ou autres_biens_2
        nb_heriters=1,
        nb_beneficiaires=1,
        lien="neveu_niece",
        versements_av_avant70=True,
        duree_max=40,
        frais_av_fixe=0.005,
        rendement_fixe=0.075
    )

    # Tu peux tester aussi :
    # lien="frere_soeur"  (35 % puis 45 % ; abattement 15 932 €)
    # lien="sans_lien"    (60 % ; abattement 1 594 €)
