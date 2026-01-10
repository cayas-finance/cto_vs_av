from dataclasses import dataclass


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
