const { simulate, collectDiffs, PS_RATE_AV } = window.SimulateCore;

const ENABLE_API_PARITY_CHECK = new URLSearchParams(window.location.search).get('compare') === '1';

const DEFAULT_FORM_VALUES = {
    capital_initial: 100000,
    duree: 20,
    rendement: 0.05,
    frais_cto: 0.0,
    rotation_rate_cto: 0.0,
    frais_av: 0.005,
    frais_gestion_pilote_av: 0.0,
    frais_versement_av: 0.0,
    rotation_rate_av: 0.0,
    frais_arbitrage_av: 0.0,
    frais_sortie_av: 0.0,
    autres_biens: 300000,
    relation: 'ligne_directe',
    nb_beneficiaires: 1,
    age_souscription: 30,
    monthly_deposit: 0,
    withdrawal_amount_monthly: 0,
    withdrawal_start_year: '',
    is_withdrawal_net: false
};

const fillResults = (res) => {
    const resultDiv = document.getElementById('result');
    resultDiv.style.display = 'block';
    resultDiv.className = res.winner === 'AV' ? 'win-av' : 'win-cto';

    document.getElementById('resWinner').textContent = res.winner;
    document.getElementById('resAdvantage').textContent = res.advantage_amount.toLocaleString('fr-FR');
    document.getElementById('resPct').textContent = res.advantage_percent;

    const cto = res.breakdown_cto;
    const av = res.breakdown_av;

    document.getElementById('cto_gross').textContent = cto.gross_capital.toLocaleString('fr-FR');
    document.getElementById('av_gross').textContent = av.gross_capital.toLocaleString('fr-FR');

    document.getElementById('cto_fees').textContent = cto.total_fees.toLocaleString('fr-FR');
    document.getElementById('av_fees').textContent = av.total_fees.toLocaleString('fr-FR');

    document.getElementById('cto_tax_withdrawals').textContent = cto.total_tax_on_withdrawals.toLocaleString('fr-FR');
    document.getElementById('av_tax_withdrawals').textContent = av.total_tax_on_withdrawals.toLocaleString('fr-FR');

    document.getElementById('cto_taxable_succ').textContent = cto.taxable_base_succession.toLocaleString('fr-FR');
    document.getElementById('av_taxable_succ').textContent = av.taxable_base_succession.toLocaleString('fr-FR');
    document.getElementById('cto_succession_gross').textContent = cto.succession_gross.toLocaleString('fr-FR');
    document.getElementById('av_succession_gross').textContent = av.succession_gross.toLocaleString('fr-FR');

    document.getElementById('scenario_cto_tax_total').textContent = cto.scenario_tax_total.toLocaleString('fr-FR');
    document.getElementById('scenario_av_rights_total').textContent = av.scenario_tax_total.toLocaleString('fr-FR');

    document.getElementById('cto_notary_fees').textContent = (cto.notary_fees || 0).toLocaleString('fr-FR');
    document.getElementById('av_notary_fees').textContent = (av.notary_fees || 0).toLocaleString('fr-FR');

    document.getElementById('scenario_av_ps_total').textContent = av.av_ps_total ? av.av_ps_total.toLocaleString('fr-FR') : '-';

    document.getElementById('scenario_cto_net_heir_total').textContent = cto.scenario_net_heir_total.toLocaleString('fr-FR');
    document.getElementById('scenario_av_net_heir_total').textContent = av.scenario_net_heir_total.toLocaleString('fr-FR');
};

document.getElementById('simForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const submitBtn = e.target.querySelector('button[type="submit"]');
    const resultDiv = document.getElementById('result');

    resultDiv.style.display = 'none';
    submitBtn.disabled = true;
    submitBtn.textContent = 'Calcul en cours...';

    const data = {
        capital_initial: parseFloat(document.getElementById('capital_initial').value),
        duree: parseInt(document.getElementById('duree').value),
        rendement: parseFloat(document.getElementById('rendement').value),
        frais_av: parseFloat(document.getElementById('frais_av').value),
        frais_gestion_pilote_av: parseFloat(document.getElementById('frais_gestion_pilote_av').value) || 0.0,
        frais_versement_av: parseFloat(document.getElementById('frais_versement_av').value) || 0.0,
        frais_arbitrage_av: parseFloat(document.getElementById('frais_arbitrage_av').value) || 0.0,
        frais_sortie_av: parseFloat(document.getElementById('frais_sortie_av').value) || 0.0,
        frais_sociaux_av: PS_RATE_AV,
        autres_biens: parseFloat(document.getElementById('autres_biens').value),
        nb_beneficiaires: parseInt(document.getElementById('nb_beneficiaires').value),
        relation: document.getElementById('relation').value,
        monthly_deposit: parseFloat(document.getElementById('monthly_deposit').value) || 0,
        withdrawal_amount: (parseFloat(document.getElementById('withdrawal_amount_monthly').value) || 0) * 12,
        withdrawal_start_year: document.getElementById('withdrawal_start_year').value ? parseInt(document.getElementById('withdrawal_start_year').value) : null,
        frais_cto: parseFloat(document.getElementById('frais_cto').value) || 0.0,
        rotation_rate_cto: parseFloat(document.getElementById('rotation_rate_cto').value) || 0.0,
        rotation_rate_av: parseFloat(document.getElementById('rotation_rate_av').value) || 0.0,
        age_souscription: parseInt(document.getElementById('age_souscription').value) || 40,
        is_withdrawal_net: document.getElementById('is_withdrawal_net').checked,
        deposit_duration_years: null,
        cto_is_donation: true
    };

    try {
        const res = simulate(data);
        fillResults(res);

        if (ENABLE_API_PARITY_CHECK) {
            const response = await fetch('/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                console.warn('API parity check failed:', response.statusText);
            } else {
                const apiRes = await response.json();
                const diffs = collectDiffs(res, apiRes);
                if (diffs.length) {
                    console.warn('Parity diffs:', diffs);
                } else {
                    console.info('API parity check: OK');
                }
            }
        }
    } catch (err) {
        alert("Erreur lors de la simulation");
        console.error(err);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Lancer la simulation';
    }
});

const applyDefaultValues = () => {
    for (const [id, value] of Object.entries(DEFAULT_FORM_VALUES)) {
        const el = document.getElementById(id);
        if (!el) {
            continue;
        }
        if (el.type === 'checkbox') {
            el.checked = Boolean(value);
        } else {
            el.value = value;
        }
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyDefaultValues);
} else {
    applyDefaultValues();
}
