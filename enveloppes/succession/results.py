from dataclasses import dataclass
from typing import Optional


@dataclass
class SuccessionCTOResult:
    succession_gross: float
    taxable_base: float
    scenario_tax_total: float
    net_heir_contract_only: float
    scenario_net_heir_total: float
    tax_attributable_cto: float
    droits_others: float
    notary_fees: float
    cto_dmtg_donation: Optional[float] = None


@dataclass
class SuccessionAVResult:
    succession_gross: float
    taxable_base: float
    scenario_tax_total: float
    scenario_net_heir_total: float
    net_heir_contract_only: float
    av_ps_total: float
    av_rights_total: float
    tax_990: float
    tax_757_marginal: float
