import numpy as np

# --- CONSTANTES FISCALES SUCCESSION ---

# Régime : ligne directe (enfants/parents)
ABATTEMENT_LIGNE_DIRECTE = 100_000
BAREME_LIGNE_DIRECTE = [
    (8_072,   0.05),
    (12_109,  0.10),
    (15_932,  0.15),
    (552_324, 0.20),
    (902_838, 0.30),
    (1_805_677, 0.40),
    (np.inf,  0.45),
]

# Régime : frères et sœurs
ABATTEMENT_FRERE_SOEUR = 15_932
BAREME_FRERE_SOEUR = [
    (24_430, 0.35),
    (np.inf,  0.45),
]

# Régime : neveux et nièces
ABATTEMENT_NEVEU_NIECE = 7_967
BAREME_NEVEU_NIECE = [(np.inf, 0.55)]

# Régime : tiers (sans lien)
ABATTEMENT_TIERS = 1_594
BAREME_TIERS = [(np.inf, 0.60)]

# --- SPÉCIFIQUE ASSURANCE-VIE ---

# Article 990 I (versements avant 70 ans)
ABATTEMENT_AV_AVANT_70 = 152_500
BAREME_AV_AVANT_70 = [
    (700_000, 0.20),
    (np.inf, 0.3125)
]

# Article 757 B (versements après 70 ans)
ABATTEMENT_AV_APRES_70_GLOBAL = 30_500

# --- FISCALITÉ DES RACHATS ---
ABATTEMENT_AV_ANNUEL_INDIVIDUEL = 4600
ABATTEMENT_AV_ANNUEL_COUPLE = 9200
PS_RATE_AV = 0.172
PS_RATE_CTO = 0.186
AV_PV_150K_THRESHOLD = 150_000
FLAT_TAX_PV_AV_AFTER_8 = 0.075
FLAT_TAX_PV_AV_BEFORE_8 = 0.128
FLAT_TAX_CTO = 0.314 # Including PS (increased in 2026)

# --- EMOLUMENTS NOTARIAUX (DONATION) ---
NOTARY_EMOLUMENTS_DONATION_BAREME = [
    (6_500, 0.04931),
    (17_000, 0.02034),
    (60_000, 0.01356),
    (np.inf, 0.01017),
]
NOTARY_EMOLUMENTS_VAT_RATE = 0.20
