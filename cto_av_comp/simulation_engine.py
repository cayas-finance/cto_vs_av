
import numpy as np
from .constants import (
    PS_RATE_AV, FLAT_TAX_CTO, FLAT_TAX_PV_AV_AFTER_8, FLAT_TAX_PV_AV_BEFORE_8,
    AV_PV_150K_THRESHOLD
)

class SimulationEngine:
    def __init__(
        self,
        capital_initial,
        rendement,
        frais_gestion_av=0.0,
        age_souscription=50,
        envelope_type="AV",
        rotation_rate_cto=0.0,
        rotation_rate_av=0.0,
        frais_versement_av=0.0,
        frais_gestion_pilote_av=0.0,
        frais_arbitrage_av=0.0,
        frais_sortie_av=0.0,
        frais_sociaux_av=PS_RATE_AV,
    ):
        self.rendement = rendement
        self.frais_gestion_av = frais_gestion_av
        self.age_souscription = age_souscription
        self.envelope_type = envelope_type
        self.rotation_rate_cto = rotation_rate_cto
        self.rotation_rate_av = rotation_rate_av
        self.frais_versement_av = frais_versement_av
        self.frais_gestion_pilote_av = frais_gestion_pilote_av
        self.frais_arbitrage_av = frais_arbitrage_av
        self.frais_sortie_av = frais_sortie_av
        self.frais_sociaux_av = frais_sociaux_av
        self.age_contrat = 0
        self.total_frais_payes = 0.0
        self.total_tax_on_gains = 0.0 # Impôts payés sur les rachats
        
        # Compartiments AV
        # Si < 70 ans à la souscription, capital initial -> 990I
        # Si >= 70 ans, capital initial -> 757B
        if self.envelope_type == "CTO":
            self.comp_990 = {
                "capital": capital_initial,
                "versements": capital_initial
            }
            self.comp_757 = {
                "capital": 0.0,
                "versements": 0.0
            }
        elif self.age_souscription < 70:
            self.comp_990 = {
                "capital": capital_initial,
                "versements": capital_initial
            }
            self.comp_757 = {
                "capital": 0.0,
                "versements": 0.0
            }
        else:
            self.comp_990 = {
                "capital": 0.0,
                "versements": 0.0
            }
            self.comp_757 = {
                "capital": capital_initial,
                "versements": capital_initial
            }
            
        # Suivi global du CTO (pas de compartiments nécessaires)
        self.prix_revient_cto = capital_initial 

    @property
    def capital(self):
        return self.comp_990["capital"] + self.comp_757["capital"]
        
    @property
    def total_versements(self):
        return self.comp_990["versements"] + self.comp_757["versements"]

    def advance_one_year(self):
        # Applique la logique aux deux compartiments
        frais_rate = self.frais_gestion_av
        if self.envelope_type == "AV":
            frais_rate += self.frais_gestion_pilote_av
        for comp in [self.comp_990, self.comp_757]:
            if comp["capital"] > 0:
                base_capital = comp["capital"]
                gain = base_capital * self.rendement
                frais = base_capital * frais_rate
                comp["capital"] = base_capital + gain - frais
                self.total_frais_payes += frais
                if self.envelope_type == "AV" and self.rotation_rate_av > 0 and self.frais_arbitrage_av > 0:
                    rotation_rate = min(1.0, max(0.0, self.rotation_rate_av))
                    frais_arbitrage = comp["capital"] * rotation_rate * self.frais_arbitrage_av
                    comp["capital"] -= frais_arbitrage
                    self.total_frais_payes += frais_arbitrage

        if self.envelope_type == "CTO" and self.rotation_rate_cto > 0 and self.capital > 0:
            rotation_rate = min(1.0, max(0.0, self.rotation_rate_cto))
            value_before_rotation = self.comp_990["capital"]
            value_sold = value_before_rotation * rotation_rate
            pru_sold = self.prix_revient_cto * rotation_rate
            pv_realisee = max(0.0, value_sold - pru_sold)
            tax_rotation = pv_realisee * FLAT_TAX_CTO

            self.comp_990["capital"] = value_before_rotation - tax_rotation
            self.prix_revient_cto = (self.prix_revient_cto * (1 - rotation_rate)) + (value_sold - tax_rotation)
        
        self.age_contrat += 1

    def deposit(self, amount, envelope_type):
        if amount <= 0: return

        # CTO : traitement standard
        if envelope_type == 'CTO':
            self.prix_revient_cto += amount
            # Pour le CTO, on stocke tout dans comp_990 pour simplifier la propriété "capital".
            # La logique de répartition concerne uniquement l'AV.
            self.comp_990["capital"] += amount
            # self.comp_990["versements"] += amount # Optionnel pour cohérence
            return

        # Logique AV
        current_age = self.age_souscription + self.age_contrat
        target_comp = self.comp_990 if current_age < 70 else self.comp_757
        
        net_amount = amount
        if envelope_type == 'AV' and self.frais_versement_av > 0:
            frais_versement = amount * self.frais_versement_av
            net_amount = amount - frais_versement
            self.total_frais_payes += frais_versement
        target_comp["capital"] += net_amount
        target_comp["versements"] += amount

    def withdraw(self, amount_gross, envelope_type, abattement_av_annuel=4600):
        if self.capital <= 0:
            return 0.0
        if amount_gross <= 0:
            return 0.0
        if amount_gross > self.capital:
            amount_gross = self.capital
        
        # Rachat au prorata des compartiments
        total_cap = self.capital
        ratio_990 = self.comp_990["capital"] / total_cap if total_cap > 0 else 0
        ratio_757 = self.comp_757["capital"] / total_cap if total_cap > 0 else 0
        
        amt_990 = amount_gross * ratio_990
        amt_757 = amount_gross * ratio_757
        
        # Mise à jour des compartiments (capital et versements)
        # Le rachat est composé d'une part capital et d'une part gain.
        # Les versements sont réduits au prorata de la valeur rachetée.
        
        tax = 0.0
        
        if envelope_type == 'CTO':
            # Logique globale CTO
            ratio_gains = max(0, (self.capital - self.prix_revient_cto) / self.capital)
            part_gains = amount_gross * ratio_gains
            part_capital = amount_gross - part_gains
            
            tax = part_gains * FLAT_TAX_CTO
            self.prix_revient_cto -= part_capital
            
            # Réduit le capital via le compartiment 990 (CTO)
            self.comp_990["capital"] -= amount_gross
            
        elif envelope_type == 'AV':
            # Logique AV globale pour l'imposition des rachats (IR/PS)
            # La règle des 70 ans concerne la succession, pas les rachats.
            # L'IR/PS s'applique sur les gains globaux.
            
            global_gains = max(0, self.capital - self.total_versements)
            ratio_gains_global = global_gains / self.capital if self.capital > 0 else 0
            
            part_gains = amount_gross * ratio_gains_global
            part_capital = amount_gross - part_gains # Part de principal restituée
            
            # Réduction des versements globaux au prorata
            # 1. Mise à jour des capitaux
            self.comp_990["capital"] -= amt_990
            self.comp_757["capital"] -= amt_757
            
            # Calcul de l'impôt
            ps = part_gains * self.frais_sociaux_av
            
            assiette_ir = part_gains
            if self.age_contrat >= 8:
                assiette_ir = max(0, part_gains - abattement_av_annuel)
                if self.total_versements <= AV_PV_150K_THRESHOLD:
                    ir = assiette_ir * FLAT_TAX_PV_AV_AFTER_8
                else:
                    ratio_low = AV_PV_150K_THRESHOLD / self.total_versements
                    assiette_low = assiette_ir * ratio_low
                    assiette_high = assiette_ir - assiette_low
                    ir = (assiette_low * FLAT_TAX_PV_AV_AFTER_8) + (assiette_high * FLAT_TAX_PV_AV_BEFORE_8)
            else:
                ir = assiette_ir * FLAT_TAX_PV_AV_BEFORE_8
            tax = ps + ir
            
        exit_fee = 0.0
        if envelope_type == 'AV' and self.frais_sortie_av > 0:
            exit_fee = amount_gross * self.frais_sortie_av
            self.total_frais_payes += exit_fee

        self.total_tax_on_gains += tax
        return amount_gross - tax - exit_fee

    def withdraw_net(self, amount_net, envelope_type, abattement_av_annuel=4600):
        # Méthode enveloppe qui appelle withdraw.
        # Conversion net -> brut à partir du ratio de gains.
        # 1. Ratio de gains global
        ratio_gains = 0.0
        if envelope_type == 'AV':
             if self.capital > 0:
                ratio_gains = max(0, (self.capital - self.total_versements) / self.capital)
        else:
             if self.capital > 0:
                ratio_gains = max(0, (self.capital - self.prix_revient_cto) / self.capital)
                
        amount_gross = amount_net
        exit_fee_rate = self.frais_sortie_av if envelope_type == 'AV' else 0.0
        
        if envelope_type == 'CTO':
             denom = 1 - (ratio_gains * FLAT_TAX_CTO)
             if denom > 0: amount_gross = amount_net / denom
        elif envelope_type == 'AV':
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
                         ir_rate = (ratio_low * FLAT_TAX_PV_AV_AFTER_8) + ((1 - ratio_low) * FLAT_TAX_PV_AV_BEFORE_8)
                 else:
                     ir_rate = FLAT_TAX_PV_AV_BEFORE_8
                 denom_complex = 1 - (ratio_gains * (self.frais_sociaux_av + ir_rate)) - exit_fee_rate
                 if denom_complex > 0:
                     abattement_tax = 0.0 if self.age_contrat < 8 else abattement_av_annuel * ir_rate
                     amount_gross = (amount_net - abattement_tax) / denom_complex
        
        if amount_gross > self.capital:
            amount_gross = self.capital
            
        self.withdraw(amount_gross, envelope_type, abattement_av_annuel)
        return amount_gross

    def force_liquidation_tax_event(self, envelope_type):
        if envelope_type == 'CTO':
             pv = max(0, self.capital - self.prix_revient_cto)
             tax = pv * FLAT_TAX_CTO
             # Déduit du capital (compartiment 990)
             self.comp_990["capital"] -= tax
             self.prix_revient_cto = self.capital
        # AV : aucun effet
            

from .model import get_regime_successoral, calcul_impot_progressif

def calculate_succession_tax_marginal(masse_taxable, autres_biens, regime_code="ligne_directe", nb_benef=1):
    abattement, bareme = get_regime_successoral(regime_code)
    
    # 1. Impôt sur les autres biens uniquement (par bénéficiaire)
    base_autres_par_benef = max(0, (autres_biens / nb_benef) - abattement)
    tax_autres = calcul_impot_progressif(base_autres_par_benef, bareme) * nb_benef
    
    # 2. Impôt total (par bénéficiaire)
    base_total_par_benef = max(0, ((autres_biens + masse_taxable) / nb_benef) - abattement)
    tax_total = calcul_impot_progressif(base_total_par_benef, bareme) * nb_benef
    
    return tax_total - tax_autres
