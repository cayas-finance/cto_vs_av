from ..core.constants import FLAT_TAX_CTO
from ..core.enveloppe_base import EnveloppeBase


class CTOSimulation(EnveloppeBase):
    def __init__(self, capital_initial, rendement, rotation_rate_cto=0.0, frais_cto=0.0):
        super().__init__(rendement)
        self.rotation_rate_cto = rotation_rate_cto
        self.frais_cto = frais_cto

        self.cto_capital = capital_initial
        self.cto_versements = capital_initial
        self.prix_revient_cto = capital_initial

    @property
    def capital(self):
        return self.cto_capital

    @property
    def total_versements(self):
        return self.cto_versements

    def _advance_one_year_impl(self):
        if self.cto_capital > 0:
            base_capital = self.cto_capital
            gain = base_capital * self.rendement
            self.cto_capital = base_capital + gain

        if self.rotation_rate_cto > 0 and self.capital > 0:
            rotation_rate = min(1.0, max(0.0, self.rotation_rate_cto))
            value_before_rotation = self.cto_capital
            value_sold = value_before_rotation * rotation_rate
            pru_sold = self.prix_revient_cto * rotation_rate
            pv_realisee = max(0.0, value_sold - pru_sold)
            tax_rotation = pv_realisee * FLAT_TAX_CTO

            self.cto_capital = value_before_rotation - tax_rotation
            self.prix_revient_cto = (
                (self.prix_revient_cto * (1 - rotation_rate))
                + (value_sold - tax_rotation)
            )

    def _deposit_impl(self, amount):
        self.prix_revient_cto += amount
        self.cto_capital += amount
        self.cto_versements += amount

    def _withdraw_impl(self, amount_gross, **_kwargs):
        ratio_gains = max(0.0, (self.capital - self.prix_revient_cto) / self.capital)
        part_gains = amount_gross * ratio_gains
        part_capital = amount_gross - part_gains

        tax = part_gains * FLAT_TAX_CTO
        self.prix_revient_cto -= part_capital
        self.cto_capital -= amount_gross

        return amount_gross - tax, tax, 0.0

    def _gross_from_net(self, amount_net, **_kwargs):
        ratio_gains = 0.0
        if self.capital > 0:
            ratio_gains = max(0.0, (self.capital - self.prix_revient_cto) / self.capital)

        denom = 1 - (ratio_gains * FLAT_TAX_CTO)
        if denom > 0:
            return amount_net / denom
        return amount_net

    def force_liquidation_tax_event(self):
        pv = max(0.0, self.capital - self.prix_revient_cto)
        tax = pv * FLAT_TAX_CTO
        self.cto_capital -= tax
        self.prix_revient_cto = self.capital
