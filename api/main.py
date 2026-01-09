from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import sys
import os

# Ajoute la racine au PYTHONPATH si besoin (optionnel en exécution module)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import des schémas
from api.schemas.simulation import SimulationRequest, SimulationResult, DetailedMetrics

# Import de la logique métier
from cto_av_comp.model import (
    get_regime_successoral,
    calcul_impot_progressif,
    calcul_emoluments_notaire
)
from cto_av_comp.simulation_engine import SimulationEngine, calculate_succession_tax_marginal
from cto_av_comp.constants import ABATTEMENT_AV_ANNUEL_INDIVIDUEL

app = FastAPI(title="CTO vs AV Simulator API")

@app.post("/simulate", response_model=SimulationResult)
def simulate(req: SimulationRequest):
    # 1. Configuration des limites
    deposit_until = req.deposit_duration_years if req.deposit_duration_years is not None else req.duree
    if req.withdrawal_start_year is not None:
        deposit_until = min(deposit_until, req.withdrawal_start_year)
    
    # --- AIDE COMMUNE : calcul des droits sur les autres biens ---
    
    # 2. Simulation CTO
    sim_cto = SimulationEngine(
        req.capital_initial,
        req.rendement,
        req.frais_cto,
        envelope_type="CTO",
        rotation_rate_cto=req.rotation_rate_cto,
    )
    total_withdrawals_net_cto = 0.0
    
    for year in range(req.duree):
        # DCA
        if year < deposit_until and req.monthly_deposit > 0:
            sim_cto.deposit(req.monthly_deposit * 12, 'CTO')
            
        # Rachats
        if req.withdrawal_start_year is not None and year >= req.withdrawal_start_year:
             if req.is_withdrawal_net:
                 sim_cto.withdraw_net(req.withdrawal_amount, 'CTO')
                 total_withdrawals_net_cto += req.withdrawal_amount 
             else:
                 net = sim_cto.withdraw(req.withdrawal_amount, 'CTO')
                 total_withdrawals_net_cto += net
             
        sim_cto.advance_one_year()
        
    # Succession CTO / Donation CTO
    abattement, bareme = get_regime_successoral(req.relation)
    base_imposable_others_par_benef = max(0, (req.autres_biens / req.nb_beneficiaires) - abattement)
    droits_others = calcul_impot_progressif(base_imposable_others_par_benef, bareme) * req.nb_beneficiaires

    succession_gross_cto = sim_cto.capital + req.autres_biens
    base_total_par_benef = max(0, (succession_gross_cto / req.nb_beneficiaires) - abattement)
    taxable_base_cto = base_total_par_benef * req.nb_beneficiaires
    droits_totaux_cto_scenario = calcul_impot_progressif(base_total_par_benef, bareme) * req.nb_beneficiaires

    dmtg_cto = None
    notary_fees_cto = 0.0
    if req.cto_is_donation:
        base_cto_par_benef = max(0, (sim_cto.capital / req.nb_beneficiaires) - abattement)
        dmtg_cto = calcul_impot_progressif(base_cto_par_benef, bareme) * req.nb_beneficiaires
        notary_fees_cto = calcul_emoluments_notaire(sim_cto.capital)
        succession_restante = max(0.0, droits_totaux_cto_scenario - dmtg_cto)
        net_heir_cto = (sim_cto.capital - dmtg_cto - notary_fees_cto) + (req.autres_biens - succession_restante)
        tax_attributable_cto = dmtg_cto
    else:
        net_heir_cto = sim_cto.capital + req.autres_biens - droits_totaux_cto_scenario
        tax_attributable_cto = droits_totaux_cto_scenario - droits_others

    net_contract_cto_only = sim_cto.capital - tax_attributable_cto - notary_fees_cto
    
    final_value_cto = net_contract_cto_only + total_withdrawals_net_cto

    # --- Simulation AV ---
    # Initialisation avec l'âge
    sim_av = SimulationEngine(
        req.capital_initial,
        req.rendement,
        req.frais_av,
        age_souscription=req.age_souscription,
        rotation_rate_av=req.rotation_rate_av,
        frais_versement_av=req.frais_versement_av,
        frais_gestion_pilote_av=req.frais_gestion_pilote_av,
        frais_arbitrage_av=req.frais_arbitrage_av,
        frais_sortie_av=req.frais_sortie_av,
        frais_sociaux_av=req.frais_sociaux_av,
    )
    total_withdrawals_net_av = 0.0
    
    for year in range(req.duree):
        # Accumulation DCA
        if year < deposit_until and req.monthly_deposit > 0:
             sim_av.deposit(req.monthly_deposit * 12, 'AV')
             
        # Rachats
        if req.withdrawal_start_year is not None and year >= req.withdrawal_start_year:
             if req.is_withdrawal_net:
                 sim_av.withdraw_net(req.withdrawal_amount, 'AV', abattement_av_annuel=ABATTEMENT_AV_ANNUEL_INDIVIDUEL)
                 total_withdrawals_net_av += req.withdrawal_amount
             else:
                 net = sim_av.withdraw(req.withdrawal_amount, 'AV', abattement_av_annuel=ABATTEMENT_AV_ANNUEL_INDIVIDUEL)
                 total_withdrawals_net_av += net
             
        sim_av.advance_one_year()
        
    # --- Fiscalité successorale AV (990I / 757B) ---
    # 1. PS (prélèvements sociaux)
    # PS dus sur les gains
    gains_av_total = max(0, sim_av.capital - sim_av.total_versements)
    ps_succ = gains_av_total * req.frais_sociaux_av
    
    # 2. Taxe 990I (versements < 70 ans)
    # Assiette = valeur de rachat (capital net de PS) proratisée
    # Fiscalité : 20% au-delà de 152 500 € par bénéficiaire
    # On détermine la part de valeur appartenant au compartiment 990I
    # Valeur_990 = Capital_Final * (Capital_990 / Capital_Total)
    valeur_990_brut = sim_av.comp_990["capital"]
    ratio_990 = valeur_990_brut / sim_av.capital if sim_av.capital > 0 else 0
    # Déduction des PS au prorata
    valeur_990_net_ps = valeur_990_brut - (ps_succ * ratio_990)
    
    abattement_990 = 152_500 * req.nb_beneficiaires
    assiette_taxable_990 = max(0, valeur_990_net_ps - abattement_990)
    # Taux forfaitaire 20% (jusqu'à 700k taxable), puis 31.25%
    # Barème appliqué par bénéficiaire
    tax_990 = 0.0
    if req.nb_beneficiaires > 0:
        masse_par_benef = assiette_taxable_990 / req.nb_beneficiaires
        if masse_par_benef > 0:
            if masse_par_benef <= 700_000:
                tax_990 = masse_par_benef * 0.20 * req.nb_beneficiaires
            else:
                tax_990 = (700_000 * 0.20 + (masse_par_benef - 700_000) * 0.3125) * req.nb_beneficiaires

    # 3. Taxe 757 B (versements >= 70 ans)
    # Seules les primes versées sont taxées. Les gains sont exonérés.
    # Si la valeur est inférieure aux primes, la valeur sert de base.
    primes_757 = sim_av.comp_757["versements"]
    valeur_757_brute = sim_av.comp_757["capital"]
    
    # Assiette brute avant abattement spécifique de 30 500 €
    base_avant_abattement_757 = min(primes_757, valeur_757_brute)
    
    # Abattement global de 30 500 € (partagé entre bénéficiaires)
    assiette_taxable_757 = max(0, base_avant_abattement_757 - 30_500)
    
    # Cette assiette s'ajoute à la succession classique (barème progressif)
    tax_757_marginal = calculate_succession_tax_marginal(
        assiette_taxable_757, 
        req.autres_biens, 
        req.relation, 
        req.nb_beneficiaires
    )
    
    # Impôt sur les autres biens uniquement (part AV)
    base_autres_par_benef = max(0, (req.autres_biens / req.nb_beneficiaires) - abattement)
    taxable_base_others = base_autres_par_benef * req.nb_beneficiaires
    tax_autres = calcul_impot_progressif(base_autres_par_benef, bareme) * req.nb_beneficiaires
    
    succession_gross_av = (sim_av.capital - ps_succ) + req.autres_biens
    taxable_base_av = taxable_base_others + assiette_taxable_990 + assiette_taxable_757

    total_tax_paid_av_scenario = tax_autres + tax_757_marginal + tax_990 + ps_succ # PS inclus dans le coût total
    
    # Droits spécifiques AV (affichage)
    droits_totaux_av_scenario = tax_990 + tax_757_marginal

    # Net AV contrat seul : capital après PS et taxes AV
    net_contract_av_only = sim_av.capital - ps_succ - tax_990 - tax_757_marginal
    
    # Net total héritiers (AV + autres biens)
    total_net_heir_av_scenario = (req.autres_biens + sim_av.capital) - total_tax_paid_av_scenario
    
    final_value_av = net_contract_av_only + total_withdrawals_net_av

    # 4. Comparaison
    
    # Lecture globale :
    # Scénario CTO : net CTO + net autres biens
    # Scénario AV : net AV + net autres biens
    
    total_net_heir_cto_scenario = net_heir_cto # Déjà calculé
    # total_net_heir_av_scenario est déjà calculé
    
    # Vérification de cohérence
    # net_contract_cto_only = sim_cto.capital - (droits_totaux_cto_scenario - droits_others)
    # total_net_heir_cto_scenario = sim_cto.capital + req.autres_biens - droits_totaux_cto_scenario
    # = sim_cto.capital - droits_totaux_cto_scenario + req.autres_biens
    # = (net_contract_cto_only + droits_totaux_cto_scenario - droits_others) - droits_totaux_cto_scenario + req.autres_biens
    # = net_contract_cto_only - droits_others + req.autres_biens.
    # Oui, cohérent.
    
    # Patrimoine global incluant les rachats
    global_wealth_cto = total_net_heir_cto_scenario + total_withdrawals_net_cto
    global_wealth_av = total_net_heir_av_scenario + total_withdrawals_net_av
    
    diff = global_wealth_av - global_wealth_cto
    max_global = max(global_wealth_av, global_wealth_cto)
    
    pct = 0.0
    if max_global > 0:
        pct = (diff / max_global) * 100
        
    winner = "AV" if diff > 0 else "CTO"
    
    return SimulationResult(
        net_cto=round(final_value_cto, 2),
        net_av=round(final_value_av, 2),
        advantage_amount=round(abs(diff), 2),
        advantage_percent=round(pct, 2),
        winner=winner,
        breakdown_cto=DetailedMetrics(
            gross_capital=round(sim_cto.capital, 2),
            total_fees=round(sim_cto.total_frais_payes, 2),
            succession_gross=round(succession_gross_cto, 2),
            taxable_base_succession=round(taxable_base_cto, 2),
            net_heir_contract_only=round(net_contract_cto_only, 2),
            scenario_tax_total=round(droits_totaux_cto_scenario, 2),
            scenario_net_heir_total=round(total_net_heir_cto_scenario, 2),
            total_tax_on_withdrawals=round(sim_cto.total_tax_on_gains, 2),
            cto_dmtg_donation=round(dmtg_cto, 2) if dmtg_cto is not None else None,
            notary_fees=round(notary_fees_cto, 2)
        ),
        breakdown_av=DetailedMetrics(
            gross_capital=round(sim_av.capital, 2),
            total_fees=round(sim_av.total_frais_payes, 2),
            succession_gross=round(succession_gross_av, 2),
            taxable_base_succession=round(taxable_base_av, 2),
            net_heir_contract_only=round(net_contract_av_only, 2),
            scenario_tax_total=round(total_tax_paid_av_scenario, 2), # Inclut PS + droits AV + droits autres biens
            scenario_net_heir_total=round(total_net_heir_av_scenario, 2),
            av_ps_total=round(ps_succ, 2),
            av_rights_total=round(droits_totaux_av_scenario, 2),
            total_tax_on_withdrawals=round(sim_av.total_tax_on_gains, 2),
            notary_fees=0.0
        )
    )

app.mount("/app", StaticFiles(directory=os.path.join(current_dir, "../ui"), html=True), name="ui")

@app.get("/")
def read_root():
    return RedirectResponse(url="/app")
