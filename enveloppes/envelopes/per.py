from ..core.enveloppe_base import EnveloppeBase


class PERSimulation(EnveloppeBase):
    # Mockup: tax rates are passed explicitly until PER rules are finalized.
    def __init__(
        self,
        capital_initial,
        rendement,
        rotation_rate_per=0.0,
        frais_per=0.0,
        tax_rate_per=0.0,
        ps_rate_per=0.0,
    ):
        super().__init__(rendement)
        self.rotation_rate_per = rotation_rate_per
        self.frais_per = frais_per
        self.tax_rate_per = tax_rate_per
        self.ps_rate_per = ps_rate_per

        self.per_capital = capital_initial
        self.per_versements = capital_initial
        self.prix_revient_per = capital_initial

    @property
    def capital(self):
        return self.per_capital

    @property
    def total_versements(self):
        return self.per_versements

    def _advance_one_year_impl(self):
        if self.per_capital > 0:
            base_capital = self.per_capital
            gain = base_capital * self.rendement
            frais = base_capital * self.frais_per
            self.per_capital = base_capital + gain - frais
            self.total_frais_payes += frais

        if self.rotation_rate_per > 0 and self.capital > 0:
            rotation_rate = min(1.0, max(0.0, self.rotation_rate_per))
            value_before_rotation = self.per_capital
            value_sold = value_before_rotation * rotation_rate
            pru_sold = self.prix_revient_per * rotation_rate
            pv_realisee = max(0.0, value_sold - pru_sold)
            tax_rotation = pv_realisee * (self.tax_rate_per + self.ps_rate_per)

            self.per_capital = value_before_rotation - tax_rotation
            self.prix_revient_per = (
                (self.prix_revient_per * (1 - rotation_rate))
                + (value_sold - tax_rotation)
            )

    def _deposit_impl(self, amount):
        self.prix_revient_per += amount
        self.per_capital += amount
        self.per_versements += amount

    def _withdraw_impl(self, amount_gross, **_kwargs):
        ratio_gains = max(0.0, (self.capital - self.prix_revient_per) / self.capital)
        part_gains = amount_gross * ratio_gains
        part_capital = amount_gross - part_gains

        tax = part_gains * (self.tax_rate_per + self.ps_rate_per)
        self.prix_revient_per -= part_capital
        self.per_capital -= amount_gross

        return amount_gross - tax, tax, 0.0

    def _gross_from_net(self, amount_net, **_kwargs):
        ratio_gains = 0.0
        if self.capital > 0:
            ratio_gains = max(0.0, (self.capital - self.prix_revient_per) / self.capital)

        denom = 1 - (ratio_gains * (self.tax_rate_per + self.ps_rate_per))
        if denom > 0:
            return amount_net / denom
        return amount_net
