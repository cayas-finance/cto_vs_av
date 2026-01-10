from ..core.fiscalite import (
    calcul_emoluments_notaire,
    calcul_impot_progressif,
    get_regime_successoral,
)
from .base import SuccessionBase
from .results import SuccessionCTOResult


class SuccessionCTO(SuccessionBase):
    def compute(
        self,
        sim,
        autres_biens,
        relation,
        nb_beneficiaires=1,
        is_donation=False,
    ) -> SuccessionCTOResult:
        nb_benef = max(1, nb_beneficiaires)
        abattement, bareme = get_regime_successoral(relation)

        base_imposable_others_par_benef = max(0, (autres_biens / nb_benef) - abattement)
        droits_others = calcul_impot_progressif(base_imposable_others_par_benef, bareme) * nb_benef

        succession_gross = sim.capital + autres_biens
        base_total_par_benef = max(0, (succession_gross / nb_benef) - abattement)
        taxable_base = base_total_par_benef * nb_benef
        droits_totaux = calcul_impot_progressif(base_total_par_benef, bareme) * nb_benef

        dmtg_cto = None
        notary_fees = 0.0
        if is_donation:
            base_cto_par_benef = max(0, (sim.capital / nb_benef) - abattement)
            dmtg_cto = calcul_impot_progressif(base_cto_par_benef, bareme) * nb_benef
            notary_fees = calcul_emoluments_notaire(sim.capital)
            succession_restante = max(0.0, droits_totaux - dmtg_cto)
            net_heir_total = (
                (sim.capital - dmtg_cto - notary_fees)
                + (autres_biens - succession_restante)
            )
            tax_attributable_cto = dmtg_cto
        else:
            net_heir_total = sim.capital + autres_biens - droits_totaux
            tax_attributable_cto = droits_totaux - droits_others

        net_contract_only = sim.capital - tax_attributable_cto - notary_fees

        return SuccessionCTOResult(
            succession_gross=succession_gross,
            taxable_base=taxable_base,
            scenario_tax_total=droits_totaux,
            net_heir_contract_only=net_contract_only,
            scenario_net_heir_total=net_heir_total,
            tax_attributable_cto=tax_attributable_cto,
            droits_others=droits_others,
            notary_fees=notary_fees,
            cto_dmtg_donation=dmtg_cto,
        )
