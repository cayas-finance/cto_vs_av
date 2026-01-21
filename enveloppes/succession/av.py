from ..core.constants import ABATTEMENT_AV_APRES_70_GLOBAL, ABATTEMENT_AV_AVANT_70
from ..core.fiscalite import (
    calcul_impot_progressif,
    calculate_succession_tax_marginal,
    get_regime_successoral,
)
from .base import SuccessionBase
from .results import SuccessionAVResult


class SuccessionAV(SuccessionBase):
    def compute(
        self,
        sim,
        autres_biens,
        relation,
        nb_beneficiaires=1,
        frais_sociaux_av=0.172,
    ) -> SuccessionAVResult:
        nb_benef = max(1, nb_beneficiaires)
        abattement, bareme = get_regime_successoral(relation)

        gains_av_total = max(0, sim.capital - sim.total_versements)
        ps_succ = gains_av_total * frais_sociaux_av

        valeur_990_brut = sim.comp_990["capital"]
        ratio_990 = valeur_990_brut / sim.capital if sim.capital > 0 else 0
        valeur_990_net_ps = valeur_990_brut - (ps_succ * ratio_990)

        abattement_990 = ABATTEMENT_AV_AVANT_70 * nb_benef
        assiette_taxable_990 = max(0, valeur_990_net_ps - abattement_990)

        tax_990 = 0.0
        masse_par_benef = assiette_taxable_990 / nb_benef if nb_benef > 0 else 0.0
        if masse_par_benef > 0:
            if masse_par_benef <= 700_000:
                tax_990 = masse_par_benef * 0.20 * nb_benef
            else:
                tax_990 = (700_000 * 0.20 + (masse_par_benef - 700_000) * 0.3125) * nb_benef

        primes_757 = sim.comp_757["versements"]
        valeur_757_brute = sim.comp_757["capital"]

        base_avant_abattement_757 = min(primes_757, valeur_757_brute)
        assiette_taxable_757 = max(0, base_avant_abattement_757 - ABATTEMENT_AV_APRES_70_GLOBAL)

        tax_757_marginal = calculate_succession_tax_marginal(
            assiette_taxable_757,
            autres_biens,
            relation,
            nb_benef,
        )

        base_autres_par_benef = max(0, (autres_biens / nb_benef) - abattement)
        taxable_base_others = base_autres_par_benef * nb_benef
        tax_autres = calcul_impot_progressif(base_autres_par_benef, bareme) * nb_benef

        succession_gross = sim.capital + autres_biens
        taxable_base = taxable_base_others + assiette_taxable_990 + assiette_taxable_757

        total_rights = tax_autres + tax_757_marginal + tax_990
        total_tax_paid = total_rights + ps_succ
        droits_totaux = tax_990 + tax_757_marginal

        net_contract_only = sim.capital - ps_succ - tax_990 - tax_757_marginal
        total_net_heir = (autres_biens + sim.capital) - total_tax_paid

        return SuccessionAVResult(
            succession_gross=succession_gross,
            taxable_base=taxable_base,
            scenario_tax_total=total_rights,
            scenario_net_heir_total=total_net_heir,
            net_heir_contract_only=net_contract_only,
            av_ps_total=ps_succ,
            av_rights_total=droits_totaux,
            tax_990=tax_990,
            tax_757_marginal=tax_757_marginal,
        )
