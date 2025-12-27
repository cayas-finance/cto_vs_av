
import numpy as np

def calculate_tax_brackets(base, brackets):
    tax = 0.0
    previous_cap = 0.0
    remaining_base = base
    
    for cap, rate in brackets:
        width = cap - previous_cap
        taxable_in_bracket = min(max(0, remaining_base), width)
        
        # If bracket is infinite
        if cap == np.inf:
            taxable_in_bracket = max(0, remaining_base)
            
        tax += taxable_in_bracket * rate
        remaining_base -= taxable_in_bracket
        previous_cap = cap
        
        if remaining_base <= 0:
            break
            
    return tax

def debug_scenario_2():
    print("\n--- DEBUG SCENARIO 2 (Actions 500k) ---")
    
    # PARAMETERS
    capital = 500_000
    others = 300_000
    duration = 15
    rate_cto = 0.095
    rate_av = 0.095 - 0.005 # 9.0%
    beneficiaries = 2
    
    # 1. GROWTH CHECK
    final_cto = capital * (1 + rate_cto)**duration
    final_av = capital * (1 + rate_av)**duration
    
    print(f"Growth Check:")
    print(f"  AV Gross: {final_av:,.0f} (Reddit: 1,821,241)") 
    # 1.821M matches nicely
    print(f"  CTO Gross: {final_cto:,.0f} (Reddit: 1,950,661)")
    # 1.950M matches nicely
    
    # 2. AV TAX ANALYSIS
    print(f"\n[AV Tax Analysis]")
    av_pv = final_av - capital
    
    # PS Calculation
    ps_rate = 0.172
    ps_amount = av_pv * ps_rate
    print(f"  PS Amount (17.2% on PV {av_pv:,.0f}): {ps_amount:,.0f}")
    
    # Reddit AV Breakdown:
    # "Droits Succession": 350,638
    # "Valeur Nette": 1,243,350
    # Implied Total Deductions = 1,821,241 - 1,243,350 = 577,891
    # If 227k is PS, then remaining "Droits" = 350k.
    # Matches Reddit's "Droits succession: 350,638".
    
    # So Reddit computes Droits = 350,638.
    # How?
    
    # Hypothesis A: Droits calculated on Gross AV (ignoring PS deduction?)
    base_taxable_gross = final_av
    per_heir_gross = base_taxable_gross / beneficiaries
    # Abatement 152,500
    taxable_gross_per_heir = max(0, per_heir_gross - 152_500)
    # Brackets AV: 20% up to 700k, 31.25% beyond
    tax_gross_per_heir = 0
    if taxable_gross_per_heir > 0:
        b1 = min(taxable_gross_per_heir, 700_000)
        b2 = max(0, taxable_gross_per_heir - 700_000)
        tax_gross_per_heir = b1 * 0.20 + b2 * 0.3125
        
    print(f"  Hypothesis A (Tax on Gross): Tax per heir on {taxable_gross_per_heir:,.0f} = {tax_gross_per_heir:,.0f}")
    print(f"  -> Total Tax Hyp A: {tax_gross_per_heir * 2:,.0f}") 
    
    # Hypothesis B: Droits calculated on Net AV (after PS)
    base_taxable_net = final_av - ps_amount # ~1.59M
    per_heir_net = base_taxable_net / beneficiaries # ~797k
    taxable_net_per_heir = max(0, per_heir_net - 152_500) # ~644k
    tax_net_per_heir = 0
    if taxable_net_per_heir > 0:
        b1 = min(taxable_net_per_heir, 700_000)
        b2 = max(0, taxable_net_per_heir - 700_000)
        tax_net_per_heir = b1 * 0.20 + b2 * 0.3125
        
    print(f"  Hypothesis B (Tax on Net of PS): Tax per heir on {taxable_net_per_heir:,.0f} = {tax_net_per_heir:,.0f}")
    print(f"  -> Total Tax Hyp B: {tax_net_per_heir * 2:,.0f}")
    
    print(f"  REDDIT SAYS: 350,638")
    
    # Difference: 350k vs 316k (Hyp A) vs 257k (Hyp B).
    # Why is Reddit higher? 
    # Maybe 990I Tax Rate is different? No 20%/31.25% is standard.
    # Maybe abatement is not applied? 
    # Try Tax on Gross WITHOUT Abatement? 
    # Try Tax on Gross with 20% flat?
    # Try Tax on Gross with 31.25% flat?
    
    # 3. CTO TAX ANALYSIS
    print(f"\n[CTO Tax Analysis]")
    # Reddit: Val 1,950,661. Droits (part CTO) 455,559.
    # Total Estate = 1.95M (CTO) + 300k (Other) = 2.25M
    # Per Heir = 1.125M
    # Abatement = 100k
    # Taxable = 1.025M
    
    # Standard Succession Brackets (Line Directe)
    brackets_succ = [
        (8072, 0.05),
        (12109, 0.10),
        (15932, 0.15),
        (552324, 0.20),
        (902838, 0.30),
        (1805677, 0.40),
        (np.inf, 0.45)
    ]
    
    tax_per_heir = calculate_tax_brackets(1_025_330, brackets_succ) # 1.125M - 100k roughly
    total_tax = tax_per_heir * 2
    
    print(f"  Estate Total: ~2.25M")
    print(f"  Taxable per heir: 1.025M")
    print(f"  Calculated Tax Per Heir: {tax_per_heir:,.0f}")
    print(f"  Total Succession Tax: {total_tax:,.0f}")
    
    # Reddit says "Droits (Part CTO)".
    # Part CTO = CTO / Total = 1.95M / 2.25M = 86.6%
    prorated_tax_cto = total_tax * (final_cto / (final_cto + others))
    
    print(f"  Prorated Tax for CTO: {prorated_tax_cto:,.0f}")
    print(f"  REDDIT SAYS: 455,559")
    
    # My calc comes to 525k * 0.86 = ~450k?
    # Actually let's be precise.
    # Estate = 1,950,661 + 300,000 = 2,250,661
    # /2 = 1,125,330.5
    # -100k = 1,025,330.5
    # Tax on 1,025,330.5:
    # 0-8k: 400
    # 8-12k: 400
    # 12-16k: 600
    # 16-552k: ~536k * 0.2 = 107k
    # 552-902k: ~350k * 0.3 = 105k
    # 902-1.025M: ~123k * 0.4 = 49k
    # Total ~262k per heir. Total 524k.
    # Ratio = 1.95 / 2.25 = 0.866
    # 524k * 0.866 = 454k.
    
    # MATCH! CTO logic is solid.
    # Conclusion: Reddit uses standard succession tax correctly for CTO.
    
    print(f"  -> CTO Match seems likely. Discrepancy in my previous run might be bracket updates or exact inputs.")

    # BACK TO AV MYSTERY
    # Reddit AV Tax = 350,638.
    # My Hyp A (Gross) = 316,000.
    # My Hyp B (Net) = 257,000.
    # Reddit is significantly HIGHER.
    # Could Reddit be applying Social Charges (17.2%) AND THEN putting the result into succession tax?
    # No, AV tax is specific (20%/31.25%).
    # Wait... is it possible he applied the WRONG bracket?
    # Or maybe he included the PS in the tax line but called it "Droits"?
    #  -> "Valeur brute: 1,821,241"
    #  -> "Plus-values: 1,321,241"
    #  -> "Droits succession: 350,638"
    #  -> "Valeur nette transmise: 1,243,350"
    #  1821 - 350 = 1471. We need to reach 1243. Gap is 228k. 
    #  228k is exactly 17.2% of 1.32M PV.
    #  So he DOES deduct PS separately (implicit).
    #  So "Droits" line is purely the 990I tax.
    
    # 350k tax on 1.8M base? ~19% effective rate.
    # Taxable base per heir (Gross) = 910k - 152k = 758k.
    # Tax = 20% of 700k (140k) + 31.25% of 58k (18k) = 158k.
    # Total = 316k.
    # Reddit = 350k.
    # Diff = 34k.
    
    # What if he forgot the abatement? 
    # 910k taxable.
    # 20% on 700k (140k) + 31.25% on 210k (65k) = 205k. Total 410k. No.
    
    # What if he applied 31.25% on EVERYTHING above 152k?
    # (758k * 0.3125) = 236k. Total 472k. No.
    
    # What if he applied 20% on EVERYTHING?
    # 758k * 0.20 = 151k. Total 302k. No.
    
    # What if he applied the tax on the WHOLE amount (no abatement)?
    # 910k * ... No.
    
    # Maybe there is a Prélèvement FORFAITAIRE libératoire old confusion?
    # No.
    
    # Let's check "Fat FIRE" scenario to help triage.
    
def debug_scenario_4():
    print("\n--- DEBUG SCENARIO 4 (Fat FIRE 5M) ---")
    
    capital = 5_000_000
    others = 1_000_000 
    duration = 15
    rate_cto = 0.095
    rate_av = 0.095 - 0.005 # 9.0%
    beneficiaries = 2
    
    final_cto = capital * (1 + rate_cto)**duration # 19.5M
    final_av = capital * (1 + rate_av)**duration # 18.2M
    
    # Reddit Results:
    # AV Tax: 5,472,879
    # CTO Tax: 8,240,325
    
    # 1. CHECK CTO TAX (My code said 11M net, he says 11M net. Wait?
    # My previous run:
    # CTO Code Net: 11,040,265.
    # Reddit CTO Net: 11,266,284.
    # Delta -226k.
    # Tax difference?
    
    # Estate = 19.5M + 1M = 20.5M.
    # Per heir 10.25M.
    # Abatement 100k -> 10.15M taxable.
    # Tax (Line Directe):
    # Mostly 45% bracket (starts at 1.8M).
    # Tax on 1.8M is ~20% average? No, progressive.
    # Max tax on 1.8M is ~400k (calculated before).
    # + 45% on (10.15M - 1.8M = 8.35M) = 3.75M.
    # Total per heir ~4.15M.
    # Total x2 = 8.3M.
    # Reddit says 8.24M.
    # Matches! (Small diff likely simpler progressive approximation).
    
    # 2. CHECK AV TAX
    # Reddit says: 5,472,879
    # Base (Gross) = 18.2M -> 9.1M per heir.
    # Taxable (Gross) = 9.1M - 152k = ~8.95M.
    # Tax: 
    # 20% on 700k = 140k.
    # 31.25% on (8.95M - 700k = 8.25M) = 2.58M.
    # Total per heir = 2.72M.
    # Total x2 = 5.44M.
    
    # Reddit says 5.47M. 
    # My Calc says 5.44M.
    # Almost perfect match! (Delta 30k on 5M tax).
    
    # SO WHERE IS THE DISCREPANCY IN NET?
    # Reddit AV Net: 10,466,999.
    # Gross 18,212,412.
    # Tax 5,472,879.
    # PS (17.2% on PV 13.2M) = 2,272,534.
    # Net = 18.2M - 5.47M - 2.27M = 10,469,533.
    # Reddit Net = 10,467,000.
    # It matches.
    
    # So why did my proper simulation return HIGHER net for AV?
    # "AV Code: 11,132,728"
    # Difference: 11.1M - 10.5M = ~600k.
    # Why is my code saving 600k tax?
    # Ah! My code calculates AV tax on NET OF PS value!
    # Reddit calculates AV tax on GROSS value (before PS).
    
    # LEGAL CHECK:
    # Article 990 I CGI: "l'assiette le montant des sommes, rentes ou valeurs dues au bénéficiaire".
    # Les prélèvements sociaux (17.2%) sont-ils déduits de l'assiette du 990 I ?
    # BOFIP (BOI-TCAS-AUT-60): "L'assiette du prélèvement est constituée par le montant des sommes... versées au bénéficiaire... NETTES de prélèvements sociaux".
    #
    # VERDICT: MY CODE IS CORRECT (Legally). REDDIT USER IS WRONG.
    # The Reddit user applies the 990I tax on the Gross amount, paying tax on the money used to pay PS.
    # That explains why his AV tax is higher, and his AV Net is lower.
    # Specifically in Scenario 4:
    # PV is huge. PS is huge (2.2M).
    # He put that 2.2M in the taxable base for 31.25% tax.
    # 2.2M * 31.25% = ~700k extra tax allowed.
    # That explains the ~600k-700k delta in Net Result.
    
    print("\n[CONCLUSION]")
    print("In Scenario 4:")
    print("Reddit AV Net: ~10.47M")
    print("My Code AV Net: ~11.13M")
    print("Delta: +660k for my code.")
    print("CAUSE:")
    print("Reddit user likely calculated 990I tax on GROSS assets.")
    print("French Law (BOFIP) states 990I tax applies to assets NET of social charges.")
    print("The PS amount (~2.2M) caused an extra ~31.25% tax (~690k) in his calc.")
    
if __name__ == "__main__":
    debug_scenario_2()
    debug_scenario_4()
