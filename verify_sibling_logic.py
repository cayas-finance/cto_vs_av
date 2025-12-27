
from CTO_vs_AV import calculer_heritage_cto, get_regime_successoral, calculer_heritage_assurance_vie

def verify_sibling_tax():
    print("=== VERIFICATION FRERE/SOEUR ===")
    
    # Check constants
    ab, bar = get_regime_successoral("frere_soeur")
    print(f"Abattement: {ab} € (Attend: 15932)")
    print(f"Barème: {bar} (Attend: 35% < 24430, 45% > 24430)")
    
    # Test Case 1: 100k Capital
    cap = 100_000
    dur = 20
    yld = 0.05
    autres = 0
    
    print(f"\n--- Simulation 100k, 20 ans, 5% ---")
    cto = calculer_heritage_cto(cap, dur, yld, autres, ab, bar)
    
    print(f"Capital Final CTO: {cto.capital_final:,.0f} €")
    print(f"Base Taxable (Cap - Abattement): {cto.capital_final - ab:,.0f} €")
    print(f"Droits Succession CTO: {cto.droits_totaux:,.0f} €")
    print(f"Taux Moyen Implicite: {cto.droits_totaux / cto.capital_final * 100:.1f} %")
    print(f"Net CTO: {cto.heritage_net:,.0f} €")
    
    # Compare with AV
    av = calculer_heritage_assurance_vie(
        cap, dur, yld, 0.005, 0.172, 152_500, [(700_000, 0.20), (float('inf'), 0.3125)]
    )
    print(f"\nAV Net: {av.heritage_net:,.0f} €")
    print(f"Diff AV vs CTO: {av.heritage_net - cto.heritage_net:,.0f} €")

if __name__ == "__main__":
    verify_sibling_tax()
