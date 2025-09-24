from dataclasses import dataclass

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

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

# ---------- Presets de succession par lien de parenté ----------
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
        abattement = 100_000
        bareme = [
            (8_072,   0.05),
            (12_109,  0.10),
            (15_932,  0.15),
            (552_324, 0.20),
            (902_838, 0.30),
            (1_805_677, 0.40),
            (np.inf,  0.45),
        ]
    elif lien in ("frere_soeur", "frère_soeur", "frere-soeur"):
        # Frères / soeurs
        abattement = 15_932
        bareme = [
            (244_430, 0.35),
            (np.inf,  0.45),
        ]
    elif lien in ("neveu_niece", "neveu-nièce", "neveu", "nièce", "niece"):
        # Neveux / nièces
        abattement = 7_967
        bareme = bareme_forfait(0.55)
    elif lien in ("sans_lien", "aucun_lien", "tiers"):
        # Tiers (sans lien de parenté)
        abattement = 1_594
        bareme = bareme_forfait(0.60)
    else:
        raise ValueError(f"Lien non reconnu: {lien}")
    return abattement, bareme

@dataclass
class AssuranceVieResult:
    heritage_net: float
    capital_final: float
    prelevements_sociaux: float
    droits_av: float


@dataclass
class CTOResult:
    heritage_net: float
    capital_final: float
    droits_imputes_cto: float
    droits_totaux: float


# ---------- Assurance-vie ----------
def calculer_heritage_assurance_vie(
    capital_initial, annee, rendement, frais_gestion, frais_sociaux,
    abattement_fiscal_av_total, bareme_av
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
    return AssuranceVieResult(
        heritage_net=heritage_net,
        capital_final=capital_final,
        prelevements_sociaux=prelevements_sociaux,
        droits_av=droits_av,
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

    actif_total = capital_final_cto + autres_biens_valeur
    base_imposable_totale = max(0.0, actif_total - abattement_succession_total)

    droits_totaux = calcul_impot_progressif(base_imposable_totale, bareme_succession)

    # Imputation proportionnelle de l'impôt au CTO
    part_cto = 0.0 if actif_total == 0 else capital_final_cto / actif_total
    droits_imputes_cto = droits_totaux * part_cto

    heritage_net = capital_final_cto - droits_imputes_cto
    return CTOResult(
        heritage_net=heritage_net,
        capital_final=capital_final_cto,
        droits_imputes_cto=droits_imputes_cto,
        droits_totaux=droits_totaux,
    )

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
        abattement_av_par_benef = 152_500
        bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    else:
        abattement_av_par_benef = 30_500
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
                abattement_fiscal_av_total, bareme_av
            )
            cto_result = calculer_heritage_cto(
                capital_initial, annees[j], rendement_fixe,
                autres_biens_valeur,
                abattement_succession_total,
                bareme_succession
            )
            base_totale = cto_result.capital_final + autres_biens_valeur
            if relatif:
                # éviter /0 : si base_totale=0 on met 0 (ou np.nan si tu préfères)
                diff_heritage1[i, j] = 0.0 if base_totale <= 0 else (av_result.heritage_net - cto_result.heritage_net) / base_totale
            else:
                diff_heritage1[i, j] = av_result.heritage_net - cto_result.heritage_net

    # --- Heatmap Rendement vs Durée (frais fixes) ---
    diff_heritage2 = np.zeros((resolution, resolution))
    for i in range(resolution):
        for j in range(resolution):
            av_result = calculer_heritage_assurance_vie(
                capital_initial, annees[j], rendements[i], frais_av_fixe, frais_sociaux_av,
                abattement_fiscal_av_total, bareme_av
            )
            cto_result = calculer_heritage_cto(
                capital_initial, annees[j], rendements[i],
                autres_biens_valeur,
                abattement_succession_total,
                bareme_succession
            )
            base_totale = cto_result.capital_final + autres_biens_valeur
            if relatif:
                diff_heritage2[i, j] = 0.0 if base_totale <= 0 else (av_result.heritage_net - cto_result.heritage_net) / base_totale
            else:
                diff_heritage2[i, j] = av_result.heritage_net - cto_result.heritage_net

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
