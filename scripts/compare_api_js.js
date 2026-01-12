#!/usr/bin/env node
const { simulate, collectDiffs } = require('../ui/simulate_core.js');

const DEFAULT_API_BASE = 'http://localhost:8001';
const DEFAULT_TOLERANCE = 0.0;
const DEFAULT_RANDOM_COUNT = 100;

const parseArgs = () => {
    const args = process.argv.slice(2);
    const options = {
        apiBase: DEFAULT_API_BASE,
        tolerance: DEFAULT_TOLERANCE,
        randomCount: DEFAULT_RANDOM_COUNT,
        seed: null,
        includeFixed: true
    };
    for (let i = 0; i < args.length; i += 1) {
        const arg = args[i];
        if (arg === '--api' && args[i + 1]) {
            options.apiBase = args[i + 1];
            i += 1;
        } else if (arg === '--tolerance' && args[i + 1]) {
            options.tolerance = Number(args[i + 1]);
            i += 1;
        } else if (arg === '--count' && args[i + 1]) {
            options.randomCount = Math.max(0, parseInt(args[i + 1], 10));
            i += 1;
        } else if (arg === '--seed' && args[i + 1]) {
            options.seed = Number(args[i + 1]);
            i += 1;
        } else if (arg === '--exact') {
            options.tolerance = 0.0;
        } else if (arg === '--only-random') {
            options.includeFixed = false;
        }
    }
    return options;
};

const buildFixedCases = () => ([
    {
        label: 'default',
        payload: {
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
            frais_sociaux_av: 0.172,
            autres_biens: 300000,
            relation: 'ligne_directe',
            nb_beneficiaires: 1,
            age_souscription: 40,
            monthly_deposit: 0,
            withdrawal_amount: 0,
            withdrawal_start_year: null,
            is_withdrawal_net: false,
            deposit_duration_years: null,
            cto_is_donation: true
        }
    },
    {
        label: 'with_withdrawals',
        payload: {
            capital_initial: 50000,
            duree: 25,
            rendement: 0.06,
            frais_cto: 0.001,
            rotation_rate_cto: 0.2,
            frais_av: 0.008,
            frais_gestion_pilote_av: 0.002,
            frais_versement_av: 0.01,
            rotation_rate_av: 0.1,
            frais_arbitrage_av: 0.001,
            frais_sortie_av: 0.005,
            frais_sociaux_av: 0.172,
            autres_biens: 150000,
            relation: 'frere_soeur',
            nb_beneficiaires: 2,
            age_souscription: 45,
            monthly_deposit: 200,
            withdrawal_amount: 6000,
            withdrawal_start_year: 15,
            is_withdrawal_net: true,
            deposit_duration_years: null,
            cto_is_donation: true
        }
    },
    {
        label: 'after_70',
        payload: {
            capital_initial: 200000,
            duree: 15,
            rendement: 0.04,
            frais_cto: 0.0,
            rotation_rate_cto: 0.0,
            frais_av: 0.004,
            frais_gestion_pilote_av: 0.0,
            frais_versement_av: 0.0,
            rotation_rate_av: 0.0,
            frais_arbitrage_av: 0.0,
            frais_sortie_av: 0.0,
            frais_sociaux_av: 0.172,
            autres_biens: 50000,
            relation: 'sans_lien',
            nb_beneficiaires: 1,
            age_souscription: 72,
            monthly_deposit: 100,
            withdrawal_amount: 0,
            withdrawal_start_year: null,
            is_withdrawal_net: false,
            deposit_duration_years: null,
            cto_is_donation: true
        }
    }
]);

const createSeededRng = (seed) => {
    if (!Number.isFinite(seed)) {
        return Math.random;
    }
    let state = (seed >>> 0) || 1;
    return () => {
        state = (1664525 * state + 1013904223) >>> 0;
        return state / 0x100000000;
    };
};

const randomInt = (rng, min, max) => Math.floor(rng() * (max - min + 1)) + min;

const randomFloat = (rng, min, max) => min + rng() * (max - min);

const randomChoice = (rng, items) => items[randomInt(rng, 0, items.length - 1)];

const buildRandomCases = (count, rng) => {
    const relations = ['ligne_directe', 'frere_soeur', 'neveu_niece', 'sans_lien'];
    const cases = [];
    for (let i = 0; i < count; i += 1) {
        const duree = randomInt(rng, 5, 40);
        const withdrawalEnabled = rng() < 0.5;
        const withdrawalStart = withdrawalEnabled ? randomInt(rng, 1, Math.max(1, duree - 1)) : null;
        const monthlyDeposit = rng() < 0.6 ? randomFloat(rng, 0, 1200) : 0;
        const withdrawalAmount = withdrawalEnabled ? randomFloat(rng, 0, 30000) : 0;

        cases.push({
            label: `random_${i + 1}`,
            payload: {
                capital_initial: randomFloat(rng, 1000, 500000),
                duree,
                rendement: randomFloat(rng, 0.0, 0.12),
                frais_cto: randomFloat(rng, 0.0, 0.01),
                rotation_rate_cto: randomFloat(rng, 0.0, 0.8),
                frais_av: randomFloat(rng, 0.0, 0.02),
                frais_gestion_pilote_av: randomFloat(rng, 0.0, 0.01),
                frais_versement_av: randomFloat(rng, 0.0, 0.05),
                rotation_rate_av: randomFloat(rng, 0.0, 0.8),
                frais_arbitrage_av: randomFloat(rng, 0.0, 0.01),
                frais_sortie_av: randomFloat(rng, 0.0, 0.05),
                frais_sociaux_av: 0.172,
                autres_biens: randomFloat(rng, 0, 500000),
                relation: randomChoice(rng, relations),
                nb_beneficiaires: randomInt(rng, 1, 4),
                age_souscription: randomInt(rng, 30, 85),
                monthly_deposit: monthlyDeposit,
                withdrawal_amount: withdrawalAmount,
                withdrawal_start_year: withdrawalStart,
                is_withdrawal_net: withdrawalEnabled ? rng() < 0.5 : false,
                deposit_duration_years: null,
                cto_is_donation: true
            }
        });
    }
    return cases;
};

const isNil = (value) => value === null || value === undefined;

const deepDiff = (local, remote, path = '', tolerance = 0.0) => {
    const diffs = [];
    const isObject = (value) => value && typeof value === 'object' && !Array.isArray(value);
    if (isNil(local) && isNil(remote)) {
        return diffs;
    }
    if (typeof local === 'number' && typeof remote === 'number') {
        if (Math.abs(local - remote) > tolerance) {
            diffs.push(`${path}: local=${local} api=${remote}`);
        }
        return diffs;
    }
    if (isObject(local) || isObject(remote)) {
        const localObj = isObject(local) ? local : {};
        const remoteObj = isObject(remote) ? remote : {};
        const keys = new Set([...Object.keys(localObj), ...Object.keys(remoteObj)]);
        for (const key of keys) {
            const nextPath = path ? `${path}.${key}` : key;
            diffs.push(...deepDiff(localObj[key], remoteObj[key], nextPath, tolerance));
        }
        return diffs;
    }
    if (local !== remote) {
        diffs.push(`${path}: local=${local} api=${remote}`);
    }
    return diffs;
};

const run = async () => {
    const { apiBase, tolerance, randomCount, seed, includeFixed } = parseArgs();
    const rng = createSeededRng(seed);
    const cases = [
        ...(includeFixed ? buildFixedCases() : []),
        ...buildRandomCases(randomCount, rng)
    ];
    let hasErrors = false;

    for (const testCase of cases) {
        const local = simulate(testCase.payload);
        const response = await fetch(`${apiBase}/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(testCase.payload)
        });
        if (!response.ok) {
            console.error(`[${testCase.label}] API error: ${response.status} ${response.statusText}`);
            hasErrors = true;
            continue;
        }
        const remote = await response.json();
        const diffs = deepDiff(local, remote, '', tolerance);
        if (diffs.length) {
            console.error(`[${testCase.label}] parity mismatch`);
            for (const diff of diffs) {
                console.error(`  - ${diff}`);
            }
            hasErrors = true;
        } else {
            console.log(`[${testCase.label}] OK`);
        }
    }

    if (hasErrors) {
        process.exitCode = 1;
    }
};

run().catch((err) => {
    console.error('Parity check failed:', err);
    process.exitCode = 1;
});
