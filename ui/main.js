// --- Simulate Core Logic ---
const ABATTEMENT_LIGNE_DIRECTE = 100000;
const BAREME_LIGNE_DIRECTE = [
    [8072, 0.05],
    [12109, 0.10],
    [15932, 0.15],
    [552324, 0.20],
    [902838, 0.30],
    [1805677, 0.40],
    [Infinity, 0.45]
];
const ABATTEMENT_FRERE_SOEUR = 15932;
const BAREME_FRERE_SOEUR = [
    [24430, 0.35],
    [Infinity, 0.45]
];
const ABATTEMENT_NEVEU_NIECE = 7967;
const BAREME_NEVEU_NIECE = [[Infinity, 0.55]];
const ABATTEMENT_TIERS = 1594;
const BAREME_TIERS = [[Infinity, 0.60]];

const ABATTEMENT_AV_APRES_70_GLOBAL = 30500;
const ABATTEMENT_AV_ANNUEL_INDIVIDUEL = 4600;
const AV_PV_150K_THRESHOLD = 150000;
const PS_RATE_AV = 0.172;
const PS_RATE_CTO = 0.186;
const FLAT_TAX_PV_AV_AFTER_8 = 0.075;
const FLAT_TAX_PV_AV_BEFORE_8 = 0.128;
const FLAT_TAX_CTO = 0.314;
const NOTARY_EMOLUMENTS_DONATION_BAREME = [
    [6500, 0.04931],
    [17000, 0.02034],
    [60000, 0.01356],
    [Infinity, 0.01017]
];
const NOTARY_EMOLUMENTS_VAT_RATE = 0.20;

const round2 = (value) => Math.round((value + Number.EPSILON) * 100) / 100;
const clamp01 = (value) => Math.min(1, Math.max(0, value));

const calculImpotProgressif = (baseImposable, bareme) => {
    if (baseImposable <= 0) return 0.0;
    let impot = 0.0;
    let prev = 0.0;
    for (const [plafond, taux] of bareme) {
        const trancheHaute = Math.min(baseImposable, plafond);
        if (trancheHaute > prev) {
            impot += (trancheHaute - prev) * taux;
            prev = trancheHaute;
        }
        if (baseImposable <= plafond) break;
    }
    return impot;
};

const calculEmolumentsNotaire = (valeur, bareme = NOTARY_EMOLUMENTS_DONATION_BAREME, tvaRate = NOTARY_EMOLUMENTS_VAT_RATE) => {
    if (valeur <= 0) return 0.0;
    const emolumentsHt = calculImpotProgressif(valeur, bareme);
    return emolumentsHt * (1 + tvaRate);
};

const getRegimeSuccessoral = (lien) => {
    const relation = (lien || '').toLowerCase();
    if (['ligne_directe', 'directe', 'enfant', 'parent-enfant'].includes(relation)) {
        return { abattement: ABATTEMENT_LIGNE_DIRECTE, bareme: BAREME_LIGNE_DIRECTE };
    }
    if (['frere_soeur', 'frère_soeur', 'frere-soeur'].includes(relation)) {
        return { abattement: ABATTEMENT_FRERE_SOEUR, bareme: BAREME_FRERE_SOEUR };
    }
    if (['neveu_niece', 'neveu-nièce', 'neveu', 'nièce', 'niece'].includes(relation)) {
        return { abattement: ABATTEMENT_NEVEU_NIECE, bareme: BAREME_NEVEU_NIECE };
    }
    if (['sans_lien', 'aucun_lien', 'tiers'].includes(relation)) {
        return { abattement: ABATTEMENT_TIERS, bareme: BAREME_TIERS };
    }
    throw new Error(`Lien non reconnu: ${lien}`);
};

const calculateSuccessionTaxMarginal = (masseTaxable, autresBiens, regimeCode = 'ligne_directe', nbBenef = 1) => {
    const { abattement, bareme } = getRegimeSuccessoral(regimeCode);
    const baseAutresParBenef = Math.max(0, (autresBiens / nbBenef) - abattement);
    const taxAutres = calculImpotProgressif(baseAutresParBenef, bareme) * nbBenef;
    const baseTotalParBenef = Math.max(0, ((autresBiens + masseTaxable) / nbBenef) - abattement);
    const taxTotal = calculImpotProgressif(baseTotalParBenef, bareme) * nbBenef;
    return taxTotal - taxAutres;
};

class SimulationEngine {
    constructor(capital_initial, rendement, frais_gestion_av = 0.0, age_souscription = 50, envelope_type = 'AV', rotation_rate_cto = 0.0, rotation_rate_av = 0.0, frais_versement_av = 0.0, frais_gestion_pilote_av = 0.0, frais_arbitrage_av = 0.0, frais_sortie_av = 0.0) {
        this.rendement = rendement;
        this.frais_gestion_av = frais_gestion_av;
        this.age_souscription = age_souscription;
        this.envelope_type = envelope_type;
        this.rotation_rate_cto = rotation_rate_cto;
        this.rotation_rate_av = rotation_rate_av;
        this.frais_versement_av = frais_versement_av;
        this.frais_gestion_pilote_av = frais_gestion_pilote_av;
        this.frais_arbitrage_av = frais_arbitrage_av;
        this.frais_sortie_av = frais_sortie_av;
        this.age_contrat = 0;
        this.total_frais_payes = 0.0;
        this.total_tax_on_gains = 0.0;

        if (this.envelope_type === 'CTO') {
            this.comp_990 = { capital: capital_initial, versements: capital_initial };
            this.comp_757 = { capital: 0.0, versements: 0.0 };
        } else if (this.age_souscription < 70) {
            this.comp_990 = { capital: capital_initial, versements: capital_initial };
            this.comp_757 = { capital: 0.0, versements: 0.0 };
        } else {
            this.comp_990 = { capital: 0.0, versements: 0.0 };
            this.comp_757 = { capital: capital_initial, versements: capital_initial };
        }
        this.prix_revient_cto = capital_initial;
    }
    get capital() { return this.comp_990.capital + this.comp_757.capital; }
    get total_versements() { return this.comp_990.versements + this.comp_757.versements; }

    advance_one_year() {
        let fraisRate = this.frais_gestion_av;
        if (this.envelope_type === 'AV') fraisRate += this.frais_gestion_pilote_av;
        for (const comp of [this.comp_990, this.comp_757]) {
            if (comp.capital > 0) {
                const baseCapital = comp.capital;
                const gain = baseCapital * this.rendement;
                const frais = baseCapital * fraisRate;
                comp.capital = baseCapital + gain - frais;
                this.total_frais_payes += frais;
                if (this.envelope_type === 'AV' && this.rotation_rate_av > 0 && this.frais_arbitrage_av > 0) {
                    const rotationRate = clamp01(this.rotation_rate_av);
                    const fraisArbitrage = comp.capital * rotationRate * this.frais_arbitrage_av;
                    comp.capital -= fraisArbitrage;
                    this.total_frais_payes += fraisArbitrage;
                }
            }
        }
        if (this.envelope_type === 'CTO' && this.rotation_rate_cto > 0 && this.capital > 0) {
            const rotationRate = clamp01(this.rotation_rate_cto);
            const valueBeforeRotation = this.comp_990.capital;
            const valueSold = valueBeforeRotation * rotationRate;
            const pruSold = this.prix_revient_cto * rotationRate;
            const pvRealisee = Math.max(0.0, valueSold - pruSold);
            const taxRotation = pvRealisee * FLAT_TAX_CTO;
            this.comp_990.capital = valueBeforeRotation - taxRotation;
            this.prix_revient_cto = (this.prix_revient_cto * (1 - rotationRate)) + (valueSold - taxRotation);
        }
        this.age_contrat += 1;
    }

    deposit(amount, envelope_type) {
        if (amount <= 0) return;
        if (envelope_type === 'CTO') {
            this.prix_revient_cto += amount;
            this.comp_990.capital += amount;
            return;
        }
        const currentAge = this.age_souscription + this.age_contrat;
        const targetComp = currentAge < 70 ? this.comp_990 : this.comp_757;
        let netAmount = amount;
        if (envelope_type === 'AV' && this.frais_versement_av > 0) {
            const fraisVersement = amount * this.frais_versement_av;
            netAmount = amount - fraisVersement;
            this.total_frais_payes += fraisVersement;
        }
        targetComp.capital += netAmount;
        targetComp.versements += amount;
    }

    withdraw(amount_gross, envelope_type, abattement_av_annuel = ABATTEMENT_AV_ANNUEL_INDIVIDUEL) {
        if (this.capital <= 0 || amount_gross <= 0) return 0.0;
        if (amount_gross > this.capital) amount_gross = this.capital;
        const totalCap = this.capital;
        const ratio_990 = totalCap > 0 ? this.comp_990.capital / totalCap : 0;
        const ratio_757 = totalCap > 0 ? this.comp_757.capital / totalCap : 0;
        const amt_990 = amount_gross * ratio_990;
        const amt_757 = amount_gross * ratio_757;
        let tax = 0.0;
        if (envelope_type === 'CTO') {
            const ratioGains = Math.max(0.0, (this.capital - this.prix_revient_cto) / this.capital);
            const partGains = amount_gross * ratioGains;
            const partCapital = amount_gross - partGains;
            tax = partGains * FLAT_TAX_CTO;
            this.prix_revient_cto -= partCapital;
            this.comp_990.capital -= amount_gross;
        } else if (envelope_type === 'AV') {
            const globalGains = Math.max(0.0, this.capital - this.total_versements);
            const ratioGainsGlobal = this.capital > 0 ? globalGains / this.capital : 0;
            const partGains = amount_gross * ratioGainsGlobal;
            this.comp_990.capital -= amt_990;
            this.comp_757.capital -= amt_757;
            const ps = partGains * PS_RATE_AV;
            let assietteIr = partGains;
            let ir = 0.0;
            if (this.age_contrat >= 8) {
                assietteIr = Math.max(0.0, partGains - abattement_av_annuel);
                if (this.total_versements <= AV_PV_150K_THRESHOLD) {
                    ir = assietteIr * FLAT_TAX_PV_AV_AFTER_8;
                } else {
                    const ratioLow = AV_PV_150K_THRESHOLD / this.total_versements;
                    const assietteLow = assietteIr * ratioLow;
                    const assietteHigh = assietteIr - assietteLow;
                    ir = (assietteLow * FLAT_TAX_PV_AV_AFTER_8) + (assietteHigh * FLAT_TAX_PV_AV_BEFORE_8);
                }
            } else {
                ir = assietteIr * FLAT_TAX_PV_AV_BEFORE_8;
            }
            tax = ps + ir;
        }
        let exitFee = 0.0;
        if (envelope_type === 'AV' && this.frais_sortie_av > 0) {
            exitFee = amount_gross * this.frais_sortie_av;
            this.total_frais_payes += exitFee;
        }
        this.total_tax_on_gains += tax;
        return amount_gross - tax - exitFee;
    }

    withdraw_net(amount_net, envelope_type, abattement_av_annuel = ABATTEMENT_AV_ANNUEL_INDIVIDUEL) {
        let ratioGains = 0.0;
        if (this.capital > 0) {
            ratioGains = envelope_type === 'AV' ? Math.max(0.0, (this.capital - this.total_versements) / this.capital) : Math.max(0.0, (this.capital - this.prix_revient_cto) / this.capital);
        }
        let amount_gross = amount_net;
        const exitFeeRate = envelope_type === 'AV' ? this.frais_sortie_av : 0.0;
        if (envelope_type === 'CTO') {
            const denom = 1 - (ratioGains * FLAT_TAX_CTO);
            if (denom > 0) amount_gross = amount_net / denom;
        } else if (envelope_type === 'AV') {
            const denomSimple = 1 - (ratioGains * PS_RATE_AV) - exitFeeRate;
            const grossSimple = denomSimple > 0 ? amount_net / denomSimple : amount_net;
            const partGainsSimple = grossSimple * ratioGains;
            if (this.age_contrat >= 8 && partGainsSimple <= abattement_av_annuel) {
                amount_gross = grossSimple;
            } else {
                let irRate = 0.0;
                if (this.age_contrat >= 8) {
                    if (this.total_versements <= AV_PV_150K_THRESHOLD) irRate = FLAT_TAX_PV_AV_AFTER_8;
                    else {
                        const ratioLow = AV_PV_150K_THRESHOLD / this.total_versements;
                        irRate = (ratioLow * FLAT_TAX_PV_AV_AFTER_8) + ((1 - ratioLow) * FLAT_TAX_PV_AV_BEFORE_8);
                    }
                } else irRate = FLAT_TAX_PV_AV_BEFORE_8;
                const denomComplex = 1 - (ratioGains * (PS_RATE_AV + irRate)) - exitFeeRate;
                if (denomComplex > 0) {
                    const abattementTax = this.age_contrat < 8 ? 0.0 : abattement_av_annuel * irRate;
                    amount_gross = (amount_net - abattementTax) / denomComplex;
                }
            }
        }
        if (amount_gross > this.capital) amount_gross = this.capital;
        this.withdraw(amount_gross, envelope_type, abattement_av_annuel);
        return amount_gross;
    }
}

const simulate = (req) => {
    let depositUntil = req.deposit_duration_years != null ? req.deposit_duration_years : req.duree;
    if (req.withdrawal_start_year != null) depositUntil = Math.min(depositUntil, req.withdrawal_start_year);

    const sim_cto = new SimulationEngine(req.capital_initial, req.rendement, req.frais_cto, 50, 'CTO', req.rotation_rate_cto);
    let total_withdrawals_net_cto = 0.0;
    for (let year = 0; year < req.duree; year += 1) {
        if (year < depositUntil && req.monthly_deposit > 0) sim_cto.deposit(req.monthly_deposit * 12, 'CTO');
        if (req.withdrawal_start_year != null && year >= req.withdrawal_start_year) {
            if (req.is_withdrawal_net) { sim_cto.withdraw_net(req.withdrawal_amount, 'CTO'); total_withdrawals_net_cto += req.withdrawal_amount; }
            else { const net = sim_cto.withdraw(req.withdrawal_amount, 'CTO'); total_withdrawals_net_cto += net; }
        }
        sim_cto.advance_one_year();
    }

    const { abattement, bareme } = getRegimeSuccessoral(req.relation);
    const base_imposable_others_par_benef = Math.max(0, (req.autres_biens / req.nb_beneficiaires) - abattement);
    const droits_others = calculImpotProgressif(base_imposable_others_par_benef, bareme) * req.nb_beneficiaires;
    const successionGrossCto = sim_cto.capital + req.autres_biens;
    const base_total_par_benef = Math.max(0, (successionGrossCto / req.nb_beneficiaires) - abattement);
    const taxableBaseCto = base_total_par_benef * req.nb_beneficiaires;
    const droits_totaux_cto_scenario = calculImpotProgressif(base_total_par_benef, bareme) * req.nb_beneficiaires;
    let net_heir_cto = 0.0, tax_attributable_cto = 0.0, dmtg_cto = null, notary_fees_cto = 0.0;
    if (req.cto_is_donation) {
        const base_cto_par_benef = Math.max(0, (sim_cto.capital / req.nb_beneficiaires) - abattement);
        dmtg_cto = calculImpotProgressif(base_cto_par_benef, bareme) * req.nb_beneficiaires;
        notary_fees_cto = calculEmolumentsNotaire(sim_cto.capital);
        const successionRestante = Math.max(0.0, droits_totaux_cto_scenario - dmtg_cto);
        tax_attributable_cto = dmtg_cto;
        net_heir_cto = (sim_cto.capital - dmtg_cto - notary_fees_cto) + (req.autres_biens - successionRestante);
    } else {
        net_heir_cto = sim_cto.capital + req.autres_biens - droits_totaux_cto_scenario;
        tax_attributable_cto = droits_totaux_cto_scenario - droits_others;
    }
    const final_value_cto = (sim_cto.capital - tax_attributable_cto - notary_fees_cto) + total_withdrawals_net_cto;

    const sim_av = new SimulationEngine(req.capital_initial, req.rendement, req.frais_av, req.age_souscription, 'AV', 0.0, req.rotation_rate_av, req.frais_versement_av, req.frais_gestion_pilote_av, req.frais_arbitrage_av, req.frais_sortie_av);
    let total_withdrawals_net_av = 0.0;
    for (let year = 0; year < req.duree; year += 1) {
        if (year < depositUntil && req.monthly_deposit > 0) sim_av.deposit(req.monthly_deposit * 12, 'AV');
        if (req.withdrawal_start_year != null && year >= req.withdrawal_start_year) {
            if (req.is_withdrawal_net) { sim_av.withdraw_net(req.withdrawal_amount, 'AV'); total_withdrawals_net_av += req.withdrawal_amount; }
            else { const net = sim_av.withdraw(req.withdrawal_amount, 'AV'); total_withdrawals_net_av += net; }
        }
        sim_av.advance_one_year();
    }
    const gains_av_total = Math.max(0, sim_av.capital - sim_av.total_versements);
    const ps_succ = gains_av_total * PS_RATE_AV;
    const valeur_990_net_ps = sim_av.comp_990.capital - (ps_succ * (sim_av.capital > 0 ? sim_av.comp_990.capital / sim_av.capital : 0));
    const tax_990 = req.nb_beneficiaires > 0 ? (() => {
        const masse_par_benef = Math.max(0, valeur_990_net_ps - (152500 * req.nb_beneficiaires)) / req.nb_beneficiaires;
        return (masse_par_benef <= 700000 ? masse_par_benef * 0.20 : (700000 * 0.20 + (masse_par_benef - 700000) * 0.3125)) * req.nb_beneficiaires;
    })() : 0;
    const tax_757_marginal = calculateSuccessionTaxMarginal(Math.max(0, Math.min(sim_av.comp_757.versements, sim_av.comp_757.capital) - ABATTEMENT_AV_APRES_70_GLOBAL), req.autres_biens, req.relation, req.nb_beneficiaires);
    const tax_autres = calculImpotProgressif(Math.max(0, (req.autres_biens / req.nb_beneficiaires) - abattement), bareme) * req.nb_beneficiaires;
    const total_rights = tax_autres + tax_757_marginal + tax_990;
    const total_tax_paid_av_scenario = total_rights + ps_succ;
    const net_contract_av_only = sim_av.capital - ps_succ - tax_990 - tax_757_marginal;
    const final_value_av = net_contract_av_only + total_withdrawals_net_av;

    const diff = (final_value_av + (req.autres_biens + sim_av.capital - total_tax_paid_av_scenario - net_contract_av_only)) - (final_value_cto + (net_heir_cto - (sim_cto.capital - tax_attributable_cto - notary_fees_cto)));
    const winner = diff > 0 ? 'AV' : 'CTO';

    return {
        net_cto: round2(final_value_cto), net_av: round2(final_value_av), advantage_amount: round2(Math.abs(diff)), advantage_percent: round2(Math.max(final_value_av, final_value_cto) > 0 ? (diff / Math.max(final_value_av, final_value_cto)) * 100 : 0), winner,
        breakdown_cto: { gross_capital: round2(sim_cto.capital), total_fees: round2(sim_cto.total_frais_payes), succession_gross: round2(successionGrossCto), taxable_base_succession: round2(taxableBaseCto), net_heir_contract_only: round2(sim_cto.capital - tax_attributable_cto - notary_fees_cto), scenario_tax_total: round2(droits_totaux_cto_scenario), scenario_net_heir_total: round2(net_heir_cto), total_tax_on_withdrawals: round2(sim_cto.total_tax_on_gains), notary_fees: round2(notary_fees_cto) },
        breakdown_av: { gross_capital: round2(sim_av.capital), total_fees: round2(sim_av.total_frais_payes), succession_gross: round2(sim_av.capital + req.autres_biens), taxable_base_succession: round2(tax_autres + tax_990 + tax_757_marginal + ps_succ), net_heir_contract_only: round2(net_contract_av_only), scenario_tax_total: round2(total_rights), scenario_net_heir_total: round2((req.autres_biens + sim_av.capital) - total_tax_paid_av_scenario), av_ps_total: round2(ps_succ), av_rights_total: round2(tax_990 + tax_757_marginal), total_tax_on_withdrawals: round2(sim_av.total_tax_on_gains), notary_fees: 0.0 }
    };
};

const collectDiffs = (local, remote, path = '') => {
    const diffs = [];
    for (const key of Object.keys(local)) {
        const nextPath = path ? `${path}.${key}` : key;
        if (local[key] && typeof local[key] === 'object' && !Array.isArray(local[key])) diffs.push(...collectDiffs(local[key], remote ? remote[key] : undefined, nextPath));
        else if (typeof local[key] === 'number' && typeof (remote ? remote[key] : undefined) === 'number') {
            if (Math.abs(local[key] - remote[key]) > 0.01) diffs.push(`${nextPath}: local=${local[key]} api=${remote[key]}`);
        } else if ((remote ? remote[key] : undefined) !== local[key]) diffs.push(`${nextPath}: local=${local[key]} api=${remote ? remote[key] : undefined}`);
    }
    return diffs;
};

// --- UI Simulation Logic ---
const DEFAULT_FORM_VALUES = {
    capital_initial: 100000, duree: 20, rendement: 0.05, frais_cto: 0.0, rotation_rate_cto: 0.0, frais_av: 0.005, frais_gestion_pilote_av: 0.0, frais_versement_av: 0.0, rotation_rate_av: 0.0, frais_arbitrage_av: 0.0, frais_sortie_av: 0.0, autres_biens: 300000, relation: 'ligne_directe', nb_beneficiaires: 1, age_souscription: 30, monthly_deposit: 0, withdrawal_amount_monthly: 0, withdrawal_start_year: '', is_withdrawal_net: false
};

const fillResults = (res) => {
    const resultDiv = document.getElementById('result');
    if (!resultDiv) return;
    resultDiv.style.display = 'block';
    resultDiv.className = res.winner === 'AV' ? 'win-av' : 'win-cto';
    [['resWinner', res.winner], ['resAdvantage', res.advantage_amount.toLocaleString('fr-FR')], ['resPct', res.advantage_percent]].forEach(([id, val]) => document.getElementById(id).textContent = val);
    const cto = res.breakdown_cto, av = res.breakdown_av;
    [['cto_gross', cto.gross_capital], ['av_gross', av.gross_capital], ['cto_fees', cto.total_fees], ['av_fees', av.total_fees], ['cto_tax_withdrawals', cto.total_tax_on_withdrawals], ['av_tax_withdrawals', av.total_tax_on_withdrawals], ['cto_taxable_succ', cto.taxable_base_succession], ['av_taxable_succ', av.taxable_base_succession], ['cto_succession_gross', cto.succession_gross], ['av_succession_gross', av.succession_gross], ['scenario_cto_tax_total', cto.scenario_tax_total], ['scenario_av_rights_total', av.scenario_tax_total], ['cto_notary_fees', cto.notary_fees || 0], ['av_notary_fees', av.notary_fees || 0], ['scenario_av_ps_total', av.av_ps_total || '-'], ['scenario_cto_net_heir_total', cto.scenario_net_heir_total], ['scenario_av_net_heir_total', av.scenario_net_heir_total]].forEach(([id, val]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = typeof val === 'number' ? val.toLocaleString('fr-FR') : val;
    });
};

const applyDefaultValues = () => {
    for (const [id, value] of Object.entries(DEFAULT_FORM_VALUES)) {
        const el = document.getElementById(id);
        if (el) { if (el.type === 'checkbox') el.checked = Boolean(value); else el.value = value; }
    }
};

const init = () => {
    applyDefaultValues();
    const formElement = document.getElementById('simForm');
    if (!formElement) { console.error('CRITICAL: #simForm not found in DOM!'); return; }
    formElement.addEventListener('submit', async function (e) {
        e.preventDefault();
        const submitBtn = e.target.querySelector('button[type="submit"]'), resultDiv = document.getElementById('result');
        if (resultDiv) resultDiv.style.display = 'none';
        if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Calcul en cours...'; }
        const data = {
            capital_initial: parseFloat(document.getElementById('capital_initial').value) || 0, duree: parseInt(document.getElementById('duree').value) || 0, rendement: parseFloat(document.getElementById('rendement').value) || 0, frais_av: parseFloat(document.getElementById('frais_av').value) || 0, frais_gestion_pilote_av: parseFloat(document.getElementById('frais_gestion_pilote_av').value) || 0.0, frais_versement_av: parseFloat(document.getElementById('frais_versement_av').value) || 0.0, frais_arbitrage_av: parseFloat(document.getElementById('frais_arbitrage_av').value) || 0.0, frais_sortie_av: parseFloat(document.getElementById('frais_sortie_av').value) || 0.0, frais_sociaux_av: PS_RATE_AV, autres_biens: parseFloat(document.getElementById('autres_biens').value) || 0, nb_beneficiaires: parseInt(document.getElementById('nb_beneficiaires').value) || 1, relation: document.getElementById('relation').value, monthly_deposit: parseFloat(document.getElementById('monthly_deposit').value) || 0, withdrawal_amount: (parseFloat(document.getElementById('withdrawal_amount_monthly').value) || 0) * 12, withdrawal_start_year: document.getElementById('withdrawal_start_year').value ? parseInt(document.getElementById('withdrawal_start_year').value) : null, frais_cto: parseFloat(document.getElementById('frais_cto').value) || 0.0, rotation_rate_cto: parseFloat(document.getElementById('rotation_rate_cto').value) || 0.0, rotation_rate_av: parseFloat(document.getElementById('rotation_rate_av').value) || 0.0, age_souscription: parseInt(document.getElementById('age_souscription').value) || 40, is_withdrawal_net: document.getElementById('is_withdrawal_net').checked, deposit_duration_years: null, cto_is_donation: true
        };
        try {
            const res = simulate(data);
            fillResults(res);
            if (new URLSearchParams(window.location.search).get('compare') === '1') {
                const response = await fetch('/simulate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
                if (response.ok) { const apiRes = await response.json(); const diffs = collectDiffs(res, apiRes); if (diffs.length) console.warn('Parity diffs:', diffs); else console.info('API parity check: OK'); }
            }
        } catch (err) { alert("Erreur lors de la simulation : " + err.message); console.error(err); }
        finally { if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Lancer la simulation'; } }
    });
};

window.onerror = (msg, url, line) => { alert(`Erreur technique : ${msg}\nLigne : ${line}\nCela peut être dû à une restriction de sécurité de votre navigateur sur les fichiers locaux.`); return false; };

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
