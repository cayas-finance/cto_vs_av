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
from enveloppes.succession.av import SuccessionAV
from enveloppes.succession.cto import SuccessionCTO
from enveloppes.envelopes.cto import CTOSimulation
from enveloppes.envelopes.av import AVSimulation
from enveloppes.core.constants import ABATTEMENT_AV_ANNUEL_INDIVIDUEL

app = FastAPI(title="CTO vs AV Simulator API")

@app.post("/simulate", response_model=SimulationResult)
def simulate(req: SimulationRequest):
    # 1. Configuration des limites
    deposit_until = req.deposit_duration_years if req.deposit_duration_years is not None else req.duree
    if req.withdrawal_start_year is not None:
        deposit_until = min(deposit_until, req.withdrawal_start_year)
    
    # --- AIDE COMMUNE : calcul des droits sur les autres biens ---
    
    # 2. Simulation CTO
    sim_cto = CTOSimulation(
        req.capital_initial,
        req.rendement,
        rotation_rate_cto=req.rotation_rate_cto,
        frais_cto=req.frais_cto,
    )
    total_withdrawals_net_cto = 0.0
    
    for year in range(req.duree):
        # DCA
        if year < deposit_until and req.monthly_deposit > 0:
            sim_cto.deposit(req.monthly_deposit * 12)
            
        # Rachats
        if req.withdrawal_start_year is not None and year >= req.withdrawal_start_year:
             if req.is_withdrawal_net:
                 sim_cto.withdraw_net(req.withdrawal_amount)
                 total_withdrawals_net_cto += req.withdrawal_amount 
             else:
                 net = sim_cto.withdraw(req.withdrawal_amount)
                 total_withdrawals_net_cto += net
             
        sim_cto.advance_one_year()
        
    succession_cto = SuccessionCTO()
    cto_metrics = succession_cto.compute(
        sim_cto,
        autres_biens=req.autres_biens,
        relation=req.relation,
        nb_beneficiaires=req.nb_beneficiaires,
        is_donation=req.cto_is_donation,
    )
    succession_gross_cto = cto_metrics.succession_gross
    taxable_base_cto = cto_metrics.taxable_base
    droits_totaux_cto_scenario = cto_metrics.scenario_tax_total
    dmtg_cto = cto_metrics.cto_dmtg_donation
    notary_fees_cto = cto_metrics.notary_fees
    net_contract_cto_only = cto_metrics.net_heir_contract_only
    total_net_heir_cto_scenario = cto_metrics.scenario_net_heir_total
    final_value_cto = net_contract_cto_only + total_withdrawals_net_cto

    # --- Simulation AV ---
    # Initialisation avec l'âge
    sim_av = AVSimulation(
        req.capital_initial,
        req.rendement,
        frais_gestion_av=req.frais_av,
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
             sim_av.deposit(req.monthly_deposit * 12)
             
        # Rachats
        if req.withdrawal_start_year is not None and year >= req.withdrawal_start_year:
             if req.is_withdrawal_net:
                 sim_av.withdraw_net(req.withdrawal_amount, abattement_av_annuel=ABATTEMENT_AV_ANNUEL_INDIVIDUEL)
                 total_withdrawals_net_av += req.withdrawal_amount
             else:
                 net = sim_av.withdraw(req.withdrawal_amount, abattement_av_annuel=ABATTEMENT_AV_ANNUEL_INDIVIDUEL)
                 total_withdrawals_net_av += net
             
        sim_av.advance_one_year()
        
    succession_av = SuccessionAV()
    av_metrics = succession_av.compute(
        sim_av,
        autres_biens=req.autres_biens,
        relation=req.relation,
        nb_beneficiaires=req.nb_beneficiaires,
        frais_sociaux_av=req.frais_sociaux_av,
    )

    succession_gross_av = av_metrics.succession_gross
    taxable_base_av = av_metrics.taxable_base
    total_tax_paid_av_scenario = av_metrics.scenario_tax_total
    droits_totaux_av_scenario = av_metrics.av_rights_total
    ps_succ = av_metrics.av_ps_total
    net_contract_av_only = av_metrics.net_heir_contract_only
    total_net_heir_av_scenario = av_metrics.scenario_net_heir_total
    final_value_av = net_contract_av_only + total_withdrawals_net_av

    # 4. Comparaison
    
    # Lecture globale :
    # Scénario CTO : net CTO + net autres biens
    # Scénario AV : net AV + net autres biens
    
    # total_net_heir_av_scenario est deja calcule
    
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
