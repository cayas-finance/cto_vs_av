from pydantic import BaseModel, Field
from typing import Optional, Dict

class SimulationRequest(BaseModel):
    capital_initial: float = Field(
        default=100_000, 
        ge=0, 
        description="Le capital initial investi au départ.",
        examples=[100_000, 500_000]
    )
    duree: int = Field(
        default=20, 
        ge=1, 
        description="La durée de la simulation en années.",
        examples=[10, 20, 30]
    )
    rendement: float = Field(
        default=0.05, 
        description="Le rendement annuel moyen espéré (net de frais de fonds, brut de frais d'enveloppe pour CTO, net de frais de gestion UC pour AV si spécifié ainsi).",
        examples=[0.03, 0.05, 0.08]
    )
    frais_av: float = Field(
        default=0.005, 
        ge=0, 
        description="Les frais de gestion annuels de l'Assurance Vie.",
        examples=[0.006, 0.005, 0.0039]
    )
    frais_cto: float = Field(
        default=0.0, 
        ge=0, 
        description="Les frais de garde annuels du Compte Titres (souvent 0).",
    )
    rotation_rate_cto: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Taux de rotation annuel du CTO (0.0 = buy & hold, 1.0 = rotation totale).",
        examples=[0.0, 0.1, 0.25]
    )
    rotation_rate_av: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Taux de rotation annuel de l'AV (0.0 = buy & hold, 1.0 = rotation totale).",
        examples=[0.0, 0.1, 0.25]
    )
    frais_sociaux_av: float = Field(
        default=0.172, 
        description="Le taux de prélèvements sociaux applicable (actuellement 17.2%).",
    )
    frais_versement_av: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Frais sur versement de l'AV (prélevés à l'entrée).",
        examples=[0.0, 0.02]
    )
    frais_gestion_pilote_av: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Frais de gestion pilotée annuels sur l'AV.",
        examples=[0.0, 0.003]
    )
    frais_arbitrage_av: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Frais d'arbitrage AV appliqués sur la part arbitrée.",
        examples=[0.0, 0.001]
    )
    frais_sortie_av: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Frais de sortie/rachat AV appliqués lors des retraits.",
        examples=[0.0, 0.01]
    )
    autres_biens: float = Field(
        default=300_000, 
        ge=0, 
        description="La valeur nette des autres biens entrant dans la succession (pour le calcul des droits marginaux).",
    )
    nb_beneficiaires: int = Field(
        default=1, 
        ge=1, 
        description="Le nombre d'héritiers/bénéficiaires.",
    )
    relation: str = Field(
        default="ligne_directe", 
        description="Le lien de parenté pour le barème successoral. Valeurs : 'ligne_directe', 'frere_soeur', 'neveu_niece', 'sans_lien'.",
        examples=["ligne_directe", "frere_soeur", "neveu_niece", "sans_lien"]
    )
    age_souscription: int = Field(
        default=40,
        ge=0,
        description="Âge de l'épargnant à la souscription (pour déterminer la fiscalité AV 70 ans).",
    )
    
    # Nouvelles options
    monthly_deposit: float = Field(
        default=0.0, 
        ge=0, 
        description="Montant du versement mensuel programmé (DCA).",
    )
    deposit_duration_years: Optional[int] = Field(
        default=None, 
        description="Durée des versements mensuels en années. Si None, dure toute la simulation.",
    )
    
    withdrawal_start_year: Optional[int] = Field(
        default=None, 
        description="Année à partir de laquelle commencer des retraits programmés (rente).",
    )
    withdrawal_amount: float = Field(
        default=0.0, 
        ge=0, 
        description="Montant du retrait annuel.",
    )
    is_withdrawal_net: bool = Field(
        default=False, 
        description="Si True, le montant du retrait visé est NET d'impôt (dans la poche). Si False, c'est un retrait BRUT (avant impôt).",
    ) # Si True, withdrawal_amount est NET (dans la poche)
    cto_is_donation: bool = Field(
        default=False,
        description="Si True, modélise une donation du CTO (DMTG appliqués sur le CTO, succession sur les autres biens uniquement).",
    )

class DetailedMetrics(BaseModel):
    # Contract Lifecycle
    gross_capital: float = Field(description="Capital brut du contrat avant fiscalité de sortie ou succession.")
    total_fees: float = Field(description="Total des frais de gestion/garde payés durant la vie du contrat.")
    
    # Succession Setup
    succession_gross: float = Field(description="Valeur brute de la succession avant impôts (contrat + autres biens).")
    taxable_base_succession: float = Field(description="Assiette soumise aux droits de succession (après abattements spécifiques AV si applicables, ou brut purge pour CTO).")
    
    # Taxes & Net Heir (Contract Only)
    net_heir_contract_only: float = Field(description="Montant net perçu par l'héritier provenant UNIQUEMENT du contrat (fiscale marginale déduite).")
    
    # Global Scenario (Contract + Other Assets)
    scenario_tax_total: float = Field(description="Droits de succession TOTAUX payés dans ce scénario (sur Contrat + Autres Biens).")
    scenario_net_heir_total: float = Field(description="Total net final perçu par les héritiers (Contrat Net + Autres Biens Net).")
    total_tax_on_withdrawals: float = Field(default=0.0, description="Impôts totaux payés sur les plus-values lors des rachats durant la vie du contrat.")
    
    # AV Specifics
    av_ps_total: Optional[float] = Field(default=None, description="Prélèvements sociaux totaux payés lors du décès (AV uniquement).")
    av_rights_total: Optional[float] = Field(default=None, description="Droits de succession (ou taxe 990I) payés sur la part AV.")
    cto_dmtg_donation: Optional[float] = Field(default=None, description="DMTG appliqués au CTO en cas de donation.")
    notary_fees: Optional[float] = Field(default=None, description="Frais de notaire (émoluments) estimés pour la donation CTO.")

class SimulationResult(BaseModel):
    net_cto: float = Field(description="Valeur nette finale héritée via CTO (après droits de succession et retraits).")
    net_av: float = Field(description="Valeur nette finale héritée via AV (après droits de succession et retraits).")
    advantage_amount: float = Field(description="Montant de l'avantage financier de la meilleure enveloppe.")
    advantage_percent: float = Field(description="Pourcentage d'avantage relatif.")
    winner: str = Field(description="L'enveloppe gagnante ('AV' ou 'CTO').")
    
    breakdown_cto: DetailedMetrics = Field(description="Détails pour le scénario CTO.")
    breakdown_av: DetailedMetrics = Field(description="Détails pour le scénario AV.")
