
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Tuple


plt.rcParams.update({
    "font.size": 14,          # taille par défaut pour tout le texte
    "axes.titlesize": 16,     # titre des axes
    "axes.labelsize": 18,     # labels x/y
    "xtick.labelsize": 12,    # ticks en x
    "ytick.labelsize": 12,    # ticks en y
    "legend.fontsize": 14,    # légendes
    "figure.titlesize": 20    # titre de la figure
})

# ---------- Barème progressif & régimes de succession ----------

def calcul_impot_progressif(base_imposable, bareme):
    if base_imposable <= 0:
        return 0.0
    imp = 0.0
    prev = 0.0
    for plafond, taux in bareme:
        tranche_haute = min(base_imposable, plafond)
        if tranche_haute > prev:
            imp += (tranche_haute - prev) * taux
            prev = tranche_haute
        if base_imposable <= plafond:
            break
    return imp

def bareme_forfait(taux):
    return [(float("inf"), taux)]

def get_regime_successoral(lien: str):
    lien = lien.lower()
    if lien in ("ligne_directe","directe","enfant","parent-enfant"):
        abattement = 100_000
        bareme = [
            (8_072,   0.05),
            (12_109,  0.10),
            (15_932,  0.15),
            (552_324, 0.20),
            (902_838, 0.30),
            (1_805_677, 0.40),
            (float("inf"), 0.45),
        ]
    elif lien in ("frere_soeur","frère_soeur","frere-soeur"):
        abattement = 15_932
        bareme = [
            (244_430, 0.35),
            (float("inf"), 0.45),
        ]
    elif lien in ("neveu_niece","neveu-nièce","neveu","nièce","niece"):
        abattement = 7_967
        bareme = bareme_forfait(0.55)
    elif lien in ("sans_lien","aucun_lien","tiers"):
        abattement = 1_594
        bareme = bareme_forfait(0.60)
    else:
        raise ValueError(f"Lien non reconnu: {lien}")
    return abattement, bareme

# ---------- Paramètres fiscaux vie ----------

@dataclass
class AVTaxParams:
    frais_gestion: float = 0.005      # 0,50%/an
    taux_sociaux: float = 0.172       # PS
    taux_ir_avant8: float = 0.128     # IR composant du PFU avant 8 ans
    taux_ir_apres8: float = 0.075     # IR composant du PFU après 8 ans (hypothèse primes <= 150k)
    abattement_apres8: float = 4600.0 # célibataire, par an sur la part gains retirée

@dataclass
class CTOTaxParams:
    taux_pfu: float = 0.128           # IR 12,8%
    taux_sociaux: float = 0.172       # PS 17,2%

# ---------- Utilitaires retraits nets ----------

def solve_gross_withdrawal_av(
    total: float, gains: float, net_target: float, year_index: int, tax: AVTaxParams
) -> Tuple[float, float, float]:
    """
    Calcule le rachat brut 'w' nécessaire pour verser 'net_target' après PS/IR.
    Hypothèse : un seul retrait en fin d'année. Part gains au prorata.
    Retourne (w, ps, ir). Si le solde est insuffisant, w=total et net_effectif<net_target.
    """
    if total <= 0 or net_target <= 0:
        return 0.0, 0.0, 0.0

    g_ratio = 0.0 if total <= 0 else max(0.0, min(1.0, gains / total))
    ts = tax.taux_sociaux

    #On considère toujours un contrat de plus de 8ans.
    tir = tax.taux_ir_apres8
    A = tax.abattement_apres8
    # Cas 1: w*g_ratio <= A  -> net = w - ts*w*g_ratio
    denom1 = 1.0 - ts * g_ratio
    w1_cap = float("inf") if g_ratio == 0 else A / g_ratio
    w1 = net_target / denom1 if denom1 > 0 else total
    # Cas 2: w*g_ratio > A   -> net = w*(1 - (ts+tir)*g_ratio) + tir*A
    denom2 = 1.0 - (ts + tir) * g_ratio
    w2 = (net_target - tir * A) / denom2 if denom2 > 0 else total
    # choisir le w cohérent avec l'inéquation
    if w1 <= w1_cap:
        w = w1
    else:
        w = max(w2, 0.0)

    w = min(w, total)  # impossible de retirer plus que le solde

    # calcul effectif des taxes pour ce w
    w_gains = w * (g_ratio if total > 0 else 0.0)
    ps = w_gains * ts
    if year_index <= 8:
        ir = w_gains * (tax.taux_ir_avant8)
    else:
        excedent = max(0.0, w_gains - tax.abattement_apres8)
        ir = excedent * (tax.taux_ir_apres8)

    return w, ps, ir

def solve_gross_withdrawal_cto(
    total: float, gains: float, net_target: float, tax: CTOTaxParams
) -> Tuple[float, float, float]:
    """
    CTO : net = w - (PS+IR)*w_gains ; w_gains = w * g_ratio
    -> w = net / (1 - g_ratio*(ts+tir))
    """
    if total <= 0 or net_target <= 0:
        return 0.0, 0.0, 0.0
    g_ratio = 0.0 if total <= 0 else max(0.0, min(1.0, gains / total))
    ts = tax.taux_sociaux
    tir = tax.taux_pfu
    denom = 1.0 - g_ratio * (ts + tir)
    w = net_target / denom if denom > 0 else total
    w = min(w, total)
    w_gains = w * g_ratio
    ps = w_gains * ts
    ir = w_gains * tir
    return w, ps, ir

# ---------- Simulations avec retraits nets ----------

def simulate_av_net(
    capital_initial: float,
    rendement_gross: float,
    years: int,
    net_target: float,
    tax: AVTaxParams
):
    r_net = max(0.0, rendement_gross - tax.frais_gestion)
    principal = float(capital_initial)
    gains = 0.0

    impots_vie = 0.0
    net_paid = 0.0

    for y in range(1, years + 1):
        total = principal + gains
        # croissance
        interest = total * r_net
        gains += interest
        total = principal + gains

        # rachat net cible
        w, ps, ir = solve_gross_withdrawal_av(total, gains, net_target, y, tax)

        g_ratio = gains / total if total > 0 else 0.0
        w_gains = w * g_ratio
        w_principal = w - w_gains

        # appliquer retrait
        gains -= w_gains
        principal -= w_principal
        impots_vie += ps + ir
        net_paid += max(0.0, w - ps - ir)

    return {
        "valeur_finale": max(0.0, principal + gains),
        "principal_restants": max(0.0, principal),
        "gains_restants": max(0.0, gains),
        "impots_payes_vie": float(impots_vie),
        "net_total_verse": float(net_paid),
    }

def simulate_cto_net(
    capital_initial: float,
    rendement_gross: float,
    years: int,
    net_target: float,
    tax: CTOTaxParams
):
    principal = float(capital_initial)
    gains = 0.0

    impots_vie = 0.0
    net_paid = 0.0

    for _ in range(1, years + 1):
        total = principal + gains
        # croissance
        interest = total * rendement_gross
        gains += interest
        total = principal + gains

        w, ps, ir = solve_gross_withdrawal_cto(total, gains, net_target, tax)

        g_ratio = gains / total if total > 0 else 0.0
        w_gains = w * g_ratio
        w_principal = w - w_gains

        gains -= w_gains
        principal -= w_principal
        impots_vie += ps + ir
        net_paid += max(0.0, w - ps - ir)

    return {
        "valeur_finale": max(0.0, principal + gains),
        "principal_restants": max(0.0, principal),
        "gains_restants": max(0.0, gains),
        "impots_payes_vie": float(impots_vie),
        "net_total_verse": float(net_paid),
    }

# ---------- Droits de succession en fin d'horizon ----------

def heritage_net_assurance_vie(
    capital_final_av: float,
    gains_restants_av: float,
    nb_beneficiaires: int,
    versements_av_avant70: bool
):
    # même hypothèse simplificatrice : PS sur gains restants, puis régime décès AV
    if versements_av_avant70:
        abattement_av_par_benef = 152_500
        bareme_av = [(700_000, 0.20), (float("inf"), 0.3125)]
    else:
        abattement_av_par_benef = 30_500
        bareme_av = [(float("inf"), 0.0)]

    taux_ps = 0.172
    capital_apres_ps = max(0.0, capital_final_av - gains_restants_av * taux_ps)

    abattement_total = abattement_av_par_benef * nb_beneficiaires
    base = max(0.0, capital_apres_ps - abattement_total)
    droits_av = calcul_impot_progressif(base, bareme_av)
    return capital_apres_ps - droits_av

def heritage_net_cto(
    capital_final_cto: float,
    autres_biens_valeur: float,
    nb_heriters: int,
    lien: str
):
    abattement_par_heritier, bareme_succession = get_regime_successoral(lien)
    abattement_total = abattement_par_heritier * nb_heriters
    actif_total = capital_final_cto + autres_biens_valeur
    base_imposable_totale = max(0.0, actif_total - abattement_total)
    droits_totaux = calcul_impot_progressif(base_imposable_totale, bareme_succession)
    part_cto = 0.0 if actif_total == 0 else capital_final_cto / actif_total
    droits_imputes_cto = droits_totaux * part_cto
    return capital_final_cto - droits_imputes_cto

# ---------- Heatmaps : mêmes grilles/axes que le script initial ----------

def heatmap_diff_frais_vs_duree(
    capital_initial=100_000,
    autres_biens_valeur=300_000,
    nb_heriters=1,
    nb_beneficiaires=1,
    lien="ligne_directe",
    versements_av_avant70=True,
    frais_sociaux_av=0.172,
    duree_max=40,
    frais_av_max=0.02,
    rendement_fixe=0.045,
    resolution=100,
    net_annuel=10_000.0,
    av_tax=AVTaxParams(),
    cto_tax=CTOTaxParams(),
    relatif=True
):
    annees = np.linspace(0, duree_max, resolution)
    frais_gestion = np.linspace(0, frais_av_max, resolution)
    Z = np.zeros((resolution, resolution))

    for i in range(resolution):
        av_tax_i = AVTaxParams(
            frais_gestion=frais_gestion[i],
            taux_sociaux=av_tax.taux_sociaux,
            taux_ir_avant8=av_tax.taux_ir_avant8,
            taux_ir_apres8=av_tax.taux_ir_apres8,
            abattement_apres8=av_tax.abattement_apres8
        )
        for j in range(resolution):
            y = int(round(annees[j]))
            if y <= 0:
                Z[i, j] = 0.0
                continue

            av_res = simulate_av_net(capital_initial, rendement_fixe, y, net_annuel, av_tax_i)
            cto_res = simulate_cto_net(capital_initial, rendement_fixe, y, net_annuel, cto_tax)

            av_herit = heritage_net_assurance_vie(
                av_res["valeur_finale"],
                av_res["gains_restants"],
                nb_beneficiaires,
                versements_av_avant70
            )
            cto_herit = heritage_net_cto(
                cto_res["valeur_finale"],
                autres_biens_valeur,
                nb_heriters,
                lien
            )
            base_totale = cto_res["valeur_finale"] + autres_biens_valeur
            Z[i, j] = 0.0 if (not relatif or base_totale <= 0) else (av_herit - cto_herit) / base_totale
            if not relatif:
                Z[i, j] = av_herit - cto_herit

    # affichage : une figure, une heatmap
    plt.figure(figsize=(10, 8))
    plt.imshow(
        Z, origin="lower",
        extent=[0, duree_max, 0, frais_av_max], aspect="auto"
    )
    plt.colorbar(label="Différence d'héritage net (relative si 'relatif')")
    plt.title(f"Impact des frais (r fixe {round(rendement_fixe*100,2)}%/an) — Retrait net {int(net_annuel)} €")
    plt.xlabel("Années de placement")
    plt.ylabel("Frais de gestion AV")
    plt.tight_layout()
    plt.show()
    return Z

def heatmap_diff_rendement_vs_duree(
    capital_initial=100_000,
    autres_biens_valeur=300_000,
    nb_heriters=1,
    nb_beneficiaires=1,
    lien="ligne_directe",
    versements_av_avant70=True,
    frais_av_fixe=0.005,
    duree_max=40,
    rendement_max=0.10,
    resolution=100,
    net_annuel=10_000.0,
    av_tax=AVTaxParams(),
    cto_tax=CTOTaxParams(),
    relatif=True
):
    annees = np.linspace(0, duree_max, resolution)
    rendements = np.linspace(0, rendement_max, resolution)
    Z = np.zeros((resolution, resolution))

    for i in range(resolution):
        av_tax_i = AVTaxParams(
            frais_gestion=frais_av_fixe,
            taux_sociaux=av_tax.taux_sociaux,
            taux_ir_avant8=av_tax.taux_ir_avant8,
            taux_ir_apres8=av_tax.taux_ir_apres8,
            abattement_apres8=av_tax.abattement_apres8
        )
        for j in range(resolution):
            y = int(round(annees[j]))
            if y <= 0:
                Z[i, j] = 0.0
                continue

            r = rendements[i]
            av_res = simulate_av_net(capital_initial, r, y, net_annuel, av_tax_i)
            cto_res = simulate_cto_net(capital_initial, r, y, net_annuel, cto_tax)

            av_herit = heritage_net_assurance_vie(
                av_res["valeur_finale"],
                av_res["gains_restants"],
                nb_beneficiaires,
                versements_av_avant70
            )
            cto_herit = heritage_net_cto(
                cto_res["valeur_finale"],
                autres_biens_valeur,
                nb_heriters,
                lien
            )
            base_totale = cto_res["valeur_finale"] + autres_biens_valeur
            Z[i, j] = 0.0 if (not relatif or base_totale <= 0) else (av_herit - cto_herit) / base_totale
            if not relatif:
                Z[i, j] = av_herit - cto_herit

    plt.figure(figsize=(10, 8))
    plt.imshow(
        Z, origin="lower",
        extent=[0, duree_max, 0, rendement_max], aspect="auto"
    )
    plt.colorbar(label="Différence d'héritage net (relative si 'relatif')")
    plt.title(f"Impact du rendement (frais fixes {round(frais_av_fixe*100,2)}%/an) — Retrait net {int(net_annuel)} €")
    plt.xlabel("Années de placement")
    plt.ylabel("Rendement annuel")
    plt.tight_layout()
    plt.show()
    return Z


def combined_heatmaps(
    capital_initial=100_000,
    autres_biens_valeur=300_000,
    nb_heriters=1,
    nb_beneficiaires=1,
    lien="ligne_directe",
    versements_av_avant70=True,
    frais_av_fixe=0.005,
    frais_av_max=0.02,
    rendement_fixe=0.045,
    rendement_max=0.10,
    duree_max=40,
    resolution=120,
    net_annuel=10_000.0,
    relatif=True,
    av_tax=AVTaxParams(),
    cto_tax=CTOTaxParams()
):
    # Build both matrices with the same backend as the heatmap_* functions
    annees = np.linspace(1, duree_max, resolution)
    frais = np.linspace(0, frais_av_max, resolution)
    rendements = np.linspace(0, rendement_max, resolution)

    # helper to simulate one cell (AV, CTO -> heritage nets), reusing net-withdraw logic
    def heritage_net_av_cto(rendement, years, frais_gestion):
        av_tax_i = AVTaxParams(
            frais_gestion=frais_gestion,
            taux_sociaux=av_tax.taux_sociaux,
            taux_ir_avant8=av_tax.taux_ir_avant8,
            taux_ir_apres8=av_tax.taux_ir_apres8,
            abattement_apres8=av_tax.abattement_apres8
        )
        av_res = simulate_av_net(capital_initial, rendement, years, net_annuel, av_tax_i)
        cto_res = simulate_cto_net(capital_initial, rendement, years, net_annuel, cto_tax)
        av_herit = heritage_net_assurance_vie(
            av_res["valeur_finale"], av_res["gains_restants"],
            nb_beneficiaires, versements_av_avant70
        )
        cto_herit = heritage_net_cto(
            cto_res["valeur_finale"], autres_biens_valeur, nb_heriters, lien
        )
        base_totale = cto_res["valeur_finale"] + autres_biens_valeur
        diff = (av_herit - cto_herit)
        if relatif:
            diff = 0.0 if base_totale <= 0 else diff / base_totale
        return diff

    Z_frais = np.zeros((resolution, resolution))
    for i, f_ in enumerate(frais):
        for j, y in enumerate(annees):
            years = int(round(y))
            if years <= 0:
                Z_frais[i, j] = 0.0
                continue
            Z_frais[i, j] = heritage_net_av_cto(rendement_fixe, years, f_)

    Z_rend = np.zeros((resolution, resolution))
    for i, r_ in enumerate(rendements):
        for j, y in enumerate(annees):
            years = int(round(y))
            if years <= 0:
                Z_rend[i, j] = 0.0
                continue
            Z_rend[i, j] = heritage_net_av_cto(r_, years, frais_av_fixe)

    # Shared normalization centered at 0 with RdYlBu
    from matplotlib.colors import TwoSlopeNorm
    vmin = float(np.nanmin([Z_frais, Z_rend]))
    vmax = float(np.nanmax([Z_frais, Z_rend]))
    norm = TwoSlopeNorm(vmin=vmin, vcenter=0.0, vmax=vmax)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

    im1 = ax1.imshow(
        Z_frais, origin="lower", extent=[0, duree_max, 0, frais_av_max],
        aspect="auto", cmap="RdYlBu", norm=norm
    )
    ax1.set_title(f"Impact des frais (r fixe : {round(rendement_fixe*100,2)}%/an) — Retrait net {int(net_annuel)} €")
    ax1.set_xlabel("Années de placement")
    ax1.set_ylabel("Frais de gestion AV (%)")

    im2 = ax2.imshow(
        Z_rend, origin="lower", extent=[0, duree_max, 0, rendement_max],
        aspect="auto", cmap="RdYlBu", norm=norm
    )
    ax2.set_title(f"Impact du rendement (frais fixes : {round(frais_av_fixe*100,2)}%/an) — Retrait net {int(net_annuel)} €")
    ax2.set_xlabel("Années de placement")
    ax2.set_ylabel("Rendement annuel (%)")

    cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(im2, ax=[ax1, ax2], fraction=0.046, pad=0.04, cax=cbar_ax)
    cbar.set_label("Différence relative d'héritage net\n(AV - CTO) / (CTO + autres biens)" if relatif else "Différence absolue d'héritage net (AV - CTO)")

    plt.tight_layout(rect=[0, 0, 0.9, 1])
    plt.show()

    return Z_frais, Z_rend


if __name__ == "__main__":
    Z_frais, Z_rend = combined_heatmaps(
        capital_initial=100_000,
        autres_biens_valeur=300_000,
        nb_heriters=1,
        nb_beneficiaires=1,
        lien="ligne_directe",
        versements_av_avant70=True,
        frais_av_fixe=0.005,  # 0,5%/an
        frais_av_max=0.02,  # 2% max
        rendement_fixe=0.045,  # 4,5%/an
        rendement_max=0.10,  # 10% max
        duree_max=40,
        resolution=150,
        net_annuel=5_000.0,
        relatif=True
    )