from ..core.constants import (
    AV_PV_150K_THRESHOLD,
    FLAT_TAX_PV_AV_AFTER_8,
    FLAT_TAX_PV_AV_BEFORE_8,
    PS_RATE_AV,
)
from ..core.enveloppe_base import EnveloppeBase


class AVSimulation(EnveloppeBase):
    def __init__(
        self,
        capital_initial,
        rendement,
        frais_gestion_av=0.0,
        age_souscription=50,
        rotation_rate_av=0.0,
        frais_versement_av=0.0,
        frais_gestion_pilote_av=0.0,
        frais_arbitrage_av=0.0,
        frais_sortie_av=0.0,
        frais_sociaux_av=PS_RATE_AV,
    ):
        super().__init__(rendement)
        self.frais_gestion_av = frais_gestion_av
        self.age_souscription = age_souscription
        self.rotation_rate_av = rotation_rate_av
        self.frais_versement_av = frais_versement_av
        self.frais_gestion_pilote_av = frais_gestion_pilote_av
        self.frais_arbitrage_av = frais_arbitrage_av
        self.frais_sortie_av = frais_sortie_av
        self.frais_sociaux_av = frais_sociaux_av

        if self.age_souscription < 70:
            self.comp_990 = {"capital": capital_initial, "versements": capital_initial}
            self.comp_757 = {"capital": 0.0, "versements": 0.0}
        else:
            self.comp_990 = {"capital": 0.0, "versements": 0.0}
            self.comp_757 = {"capital": capital_initial, "versements": capital_initial}

    @property
    def capital(self):
        return self.comp_990["capital"] + self.comp_757["capital"]

    @property
    def total_versements(self):
        return self.comp_990["versements"] + self.comp_757["versements"]

    def _advance_one_year_impl(self):
        frais_rate = self.frais_gestion_av + self.frais_gestion_pilote_av
        for comp in [self.comp_990, self.comp_757]:
            if comp["capital"] > 0:
                base_capital = comp["capital"]
                gain = base_capital * self.rendement
                frais = base_capital * frais_rate
                comp["capital"] = base_capital + gain - frais
                self.total_frais_payes += frais

                if self.rotation_rate_av > 0 and self.frais_arbitrage_av > 0:
                    rotation_rate = min(1.0, max(0.0, self.rotation_rate_av))
                    frais_arbitrage = comp["capital"] * rotation_rate * self.frais_arbitrage_av
                    comp["capital"] -= frais_arbitrage
                    self.total_frais_payes += frais_arbitrage

    def _deposit_impl(self, amount):
        current_age = self.age_souscription + self.age_contrat
        target_comp = self.comp_990 if current_age < 70 else self.comp_757

        net_amount = amount
        if self.frais_versement_av > 0:
            frais_versement = amount * self.frais_versement_av
            net_amount = amount - frais_versement
            self.total_frais_payes += frais_versement

        target_comp["capital"] += net_amount
        target_comp["versements"] += amount

    def _withdraw_impl(self, amount_gross, abattement_av_annuel=4600, **_kwargs):
        total_cap = self.capital
        ratio_990 = self.comp_990["capital"] / total_cap if total_cap > 0 else 0
        ratio_757 = self.comp_757["capital"] / total_cap if total_cap > 0 else 0

        amt_990 = amount_gross * ratio_990
        amt_757 = amount_gross * ratio_757

        global_gains = max(0.0, self.capital - self.total_versements)
        ratio_gains_global = global_gains / self.capital if self.capital > 0 else 0
        part_gains = amount_gross * ratio_gains_global

        self.comp_990["capital"] -= amt_990
        self.comp_757["capital"] -= amt_757

        ps = part_gains * self.frais_sociaux_av

        assiette_ir = part_gains
        if self.age_contrat >= 8:
            assiette_ir = max(0.0, part_gains - abattement_av_annuel)
            if self.total_versements <= AV_PV_150K_THRESHOLD:
                ir = assiette_ir * FLAT_TAX_PV_AV_AFTER_8
            else:
                ratio_low = AV_PV_150K_THRESHOLD / self.total_versements
                assiette_low = assiette_ir * ratio_low
                assiette_high = assiette_ir - assiette_low
                ir = (assiette_low * FLAT_TAX_PV_AV_AFTER_8) + (
                    assiette_high * FLAT_TAX_PV_AV_BEFORE_8
                )
        else:
            ir = assiette_ir * FLAT_TAX_PV_AV_BEFORE_8

        tax = ps + ir

        exit_fee = 0.0
        if self.frais_sortie_av > 0:
            exit_fee = amount_gross * self.frais_sortie_av

        return amount_gross - tax - exit_fee, tax, exit_fee

    def _gross_from_net(self, amount_net, abattement_av_annuel=4600, **_kwargs):
        ratio_gains = 0.0
        if self.capital > 0:
            ratio_gains = max(0.0, (self.capital - self.total_versements) / self.capital)

        amount_gross = amount_net
        exit_fee_rate = self.frais_sortie_av

        denom_simple = 1 - (ratio_gains * self.frais_sociaux_av) - exit_fee_rate
        gross_simple = amount_net / denom_simple if denom_simple > 0 else amount_net
        part_gains_simple = gross_simple * ratio_gains

        if self.age_contrat >= 8 and part_gains_simple <= abattement_av_annuel:
            amount_gross = gross_simple
        else:
            if self.age_contrat >= 8:
                if self.total_versements <= AV_PV_150K_THRESHOLD:
                    ir_rate = FLAT_TAX_PV_AV_AFTER_8
                else:
                    ratio_low = AV_PV_150K_THRESHOLD / self.total_versements
                    ir_rate = (ratio_low * FLAT_TAX_PV_AV_AFTER_8) + (
                        (1 - ratio_low) * FLAT_TAX_PV_AV_BEFORE_8
                    )
            else:
                ir_rate = FLAT_TAX_PV_AV_BEFORE_8

            denom_complex = 1 - (ratio_gains * (self.frais_sociaux_av + ir_rate)) - exit_fee_rate
            if denom_complex > 0:
                abattement_tax = 0.0 if self.age_contrat < 8 else abattement_av_annuel * ir_rate
                amount_gross = (amount_net - abattement_tax) / denom_complex

        return amount_gross
