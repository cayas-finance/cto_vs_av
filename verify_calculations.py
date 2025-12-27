
from CTO_vs_AV import (
    calculer_heritage_assurance_vie,
    get_regime_successoral,
    AssuranceVieResult
)
import numpy as np

def verify_av_plus_70():
    print("--- Verification AV > 70 ans ---")
    
    # Cas de test : 
    # Capital initial : 100 000 €
    # Rendement : 0% (pour n'avoir aucune plus-value et tester uniquement la transmission du capital)
    # Frais : 0%
    # Durée : 1 an
    # Bénéficiaire : 1 (Ligne directe)
    # Versements > 70 ans : OUI
    
    capital = 100_000
    rendement = 0.0
    frais = 0.0
    frais_sociaux = 0.172
    nb_beneficiaires = 1
    
    # Setup pour > 70 ans tel que défini dans le code actuel (app.py:64)
    # "versements_av_avant70": False  <-- Correction: Si versements APRES 70 ans, le booléen 'versements_av_avant70' est False
    
    # Dans le code app.py : 
    # if inputs.versements_av_avant70: ... else: ...
    # Donc pour tester APRES 70 ans, on met False.
    
    versements_avant_70 = False 
    
    if versements_avant_70:
        abattement_av = 152_500
        bareme_av = [(700_000, 0.20), (np.inf, 0.3125)]
    else:
        # C'est ici que je suspecte le problème.
        # Le code actuel dit :
        abattement_av = 30_500
        bareme_av = [(np.inf, 0.0)] # Taux 0% ???
        
    abattement_total = abattement_av * nb_beneficiaires
    
    result = calculer_heritage_assurance_vie(
        capital, 1, rendement, frais, frais_sociaux,
        abattement_total, bareme_av,
        versement_apres_70=(not versements_avant_70)
    )
    
    print(f"Versements AVANT 70 ans ? {versements_avant_70}")
    print(f"Capital Initial: {capital}")
    print(f"Capital Final (avant succession): {result.capital_final}")
    print(f"Abattement utilisé: {abattement_total}")
    print(f"Droits AV calculés par le code (990 I): {result.droits_av}")
    print(f"Montant soumis à succession (757 B): {result.montant_soumis_succession}")
    print(f"Héritage Net (Hors 757B): {result.heritage_net}")
    
    # Calcul théorique attendu (Fiscalité Française)
    # Primes > 70 ans : 
    # - Abattement global 30 500 € (tous contrats/bénéficiaires confondus)
    # - Le surplus est réintégré à l'actif successoral et taxé aux droits de succession (DMTG)
    # - Les intérêts/plus-values sont EXONÉRÉS.
    
    # Ici rendement 0%, donc pas de gains. Tout est prime.
    # Assiette taxable = 100 000 - 30 500 = 69 500 €
    # Cette assiette devrait être taxée au barème successoral (Ligne directe).
    # Barème ligne directe (après abattement 100k€ si disponible, mais ici on regarde juste si un impôt est généré)
    # ATTENTION : En réalité, cela s'ajoute aux autres biens.
    # Si c'était le seul bien : 69 500 < 100 000 (abattement succession ligne directe). Donc 0 impôt.
    
    # Pour voir un impôt, il faut simuler que l'abattement succession est déjà mangé par "autres biens" ou dépassé.
    # MAIS `calculer_heritage_assurance_vie` dans ce code NE CONNAIT PAS les autres biens ni le barème succession.
    # C'est une fonction isolée.
    # Donc si elle renvoie "Droits AV = 0", elle dit "Pas de prélèvement spécifique AV". C'est techniquement vrai pour le 757B.
    # MAIS, `calculer_heritage_cto` lui applique le barème succession.
    
    # LE PROBLEME DE CONCEPTION : 
    # Pour les primes > 70 ans (757B), la taxation N'EST PAS un prélèvement forfaitaire AV isolé.
    # C'est une réintégration à la succession.
    # Le code actuel calcule "Droits AV" à part.
    # Si le code renvoie 0 droits AV, c'est ""juste"" au sens du prélèvement 990I.
    # MAIS il faut que ces sommes soient ajoutées à la base taxable succession ailleurs.
    
    # Vérifions `app.py` -> `compute_comparison` pour voir comment c'est assemblé.
    
if __name__ == "__main__":
    verify_av_plus_70()
