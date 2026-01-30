from ..core.enveloppe_base import EnveloppeBase


class PEASimulation(EnveloppeBase):
    # Mockup: tax rates are passed explicitly until PEA rules are finalized.
    def __init__(
        self,
        capital_initial,
        rendement,
        rotation_rate_pea=0.0,
        frais_pea=0.0,
        tax_rate_pea=0.0,
        ps_rate_pea=0.0,
    ):
        super().__init__(rendement)
        self.rotation_rate_pea = rotation_rate_pea
        self.frais_pea = frais_pea
        self.tax_rate_pea = tax_rate_pea
        self.ps_rate_pea = ps_rate_pea

        self.pea_capital = capital_initial
        self.pea_versements = capital_initial
        self.prix_revient_pea = capital_initial

    @property
    def capital(self):
        return self.pea_capital

    @property
    def total_versements(self):
        return self.pea_versements

    def _advance_one_year_impl(self):
        if self.pea_capital > 0:
            base_capital = self.pea_capital
            gain = base_capital * self.rendement
            frais = base_capital * self.frais_pea
            self.pea_capital = base_capital + gain - frais
            self.total_frais_payes += frais

        if self.rotation_rate_pea > 0 and self.capital > 0:
            rotation_rate = min(1.0, max(0.0, self.rotation_rate_pea))
            value_before_rotation = self.pea_capital
            value_sold = value_before_rotation * rotation_rate
            pru_sold = self.prix_revient_pea * rotation_rate
            pv_realisee = max(0.0, value_sold - pru_sold)
            tax_rotation = pv_realisee * (self.tax_rate_pea + self.ps_rate_pea)

            self.pea_capital = value_before_rotation - tax_rotation
            self.prix_revient_pea = (
                (self.prix_revient_pea * (1 - rotation_rate))
                + (value_sold - tax_rotation)
            )

    def _deposit_impl(self, amount):
        self.prix_revient_pea += amount
        self.pea_capital += amount
        self.pea_versements += amount

    def _withdraw_impl(self, amount_gross, **_kwargs):
        ratio_gains = max(0.0, (self.capital - self.prix_revient_pea) / self.capital)
        part_gains = amount_gross * ratio_gains
        part_capital = amount_gross - part_gains

        tax = part_gains * (self.tax_rate_pea + self.ps_rate_pea)
        self.prix_revient_pea -= part_capital
        self.pea_capital -= amount_gross

        return amount_gross - tax, tax, 0.0

    def _gross_from_net(self, amount_net, **_kwargs):
        ratio_gains = 0.0
        if self.capital > 0:
            ratio_gains = max(0.0, (self.capital - self.prix_revient_pea) / self.capital)

        denom = 1 - (ratio_gains * (self.tax_rate_pea + self.ps_rate_pea))
        if denom > 0:
            return amount_net / denom
        return amount_net
