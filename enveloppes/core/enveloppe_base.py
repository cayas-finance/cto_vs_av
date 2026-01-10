class EnveloppeBase:
    def __init__(self, rendement):
        self.rendement = rendement
        self.age_contrat = 0
        self.total_frais_payes = 0.0
        self.total_tax_on_gains = 0.0

    @property
    def capital(self):
        raise NotImplementedError

    @property
    def total_versements(self):
        raise NotImplementedError

    def advance_one_year(self):
        self._advance_one_year_impl()
        self.age_contrat += 1

    def _advance_one_year_impl(self):
        raise NotImplementedError

    def deposit(self, amount):
        if amount <= 0:
            return
        self._deposit_impl(amount)

    def _deposit_impl(self, amount):
        raise NotImplementedError

    def withdraw(self, amount_gross, **kwargs):
        if self.capital <= 0:
            return 0.0
        if amount_gross <= 0:
            return 0.0
        if amount_gross > self.capital:
            amount_gross = self.capital

        net, tax, fees = self._withdraw_impl(amount_gross, **kwargs)
        self.total_tax_on_gains += tax
        self.total_frais_payes += fees
        return net

    def _withdraw_impl(self, amount_gross, **kwargs):
        raise NotImplementedError

    def withdraw_net(self, amount_net, **kwargs):
        if self.capital <= 0:
            return 0.0
        if amount_net <= 0:
            return 0.0

        amount_gross = self._gross_from_net(amount_net, **kwargs)
        if amount_gross > self.capital:
            amount_gross = self.capital

        self.withdraw(amount_gross, **kwargs)
        return amount_gross

    def _gross_from_net(self, amount_net, **kwargs):
        raise NotImplementedError

    def force_liquidation_tax_event(self):
        return
