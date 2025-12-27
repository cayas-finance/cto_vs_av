import numpy as np

# Fonction pour calculer la valeur future d'un investissement avec des frais de gestion annuels
def valeur_future_avec_frais(principal, taux_rendement, frais_gestion, annees):
    taux_net = taux_rendement - frais_gestion
    return principal * (1 + taux_net) ** annees

# Fonction pour calculer les frais de succession pour l'AV
def frais_success_av(principal, montant, annees):
    # Calculer les gains
    gain = montant - principal

    # Appliquer les prélèvements sociaux (17.2%)
    montant_apres_prelevements = montant - (gain * (0.172))
    # Appliquer le barème spécifique des successions de l'AV
    abattement = 152500
    montant_imposable = max(0, montant_apres_prelevements - abattement)

    # Calculer la taxe selon le barème spécifique
    taxe = 0
    if montant_imposable > 0:
        if montant_imposable <= 700000:  # 852500 - 152500
            taxe = montant_imposable * 0.20
        else:
            taxe = 700000 * 0.20 + (montant_imposable - 700000) * 0.3125
    return taxe, gain, montant_apres_prelevements, montant_imposable

# Fonction pour calculer les frais de succession pour le CTO
def frais_success_cto(montant_total):
    # Abattement de 100 000 € par enfant
    abattement = 100000
    montant_imposable = max(0, montant_total - abattement)

    # Calcul des droits de succession selon les tranches progressives
    taxe = 0
    if montant_imposable > 0:
        if montant_imposable <= 8072:
            taxe = montant_imposable * 0.05
        elif montant_imposable <= 12109:
            taxe = 8072 * 0.05 + (montant_imposable - 8072) * 0.10
        elif montant_imposable <= 15932:
            taxe = 8072 * 0.05 + (12109 - 8072) * 0.10 + (montant_imposable - 12109) * 0.15
        elif montant_imposable <= 552324:
            taxe = 8072 * 0.05 + (12109 - 8072) * 0.10 + (15932 - 12109) * 0.15 + (montant_imposable - 15932) * 0.20
        elif montant_imposable <= 902838:
            taxe = 8072 * 0.05 + (12109 - 8072) * 0.10 + (15932 - 12109) * 0.15 + (552324 - 15932) * 0.20 + (montant_imposable - 552324) * 0.30
        elif montant_imposable <= 1805677:
            taxe = 8072 * 0.05 + (12109 - 8072) * 0.10 + (15932 - 12109) * 0.15 + (552324 - 15932) * 0.20 + (902838 - 552324) * 0.30 + (montant_imposable - 902838) * 0.40
        else:
            taxe = 8072 * 0.05 + (12109 - 8072) * 0.10 + (15932 - 12109) * 0.15 + (552324 - 15932) * 0.20 + (902838 - 552324) * 0.30 + (1805677 - 902838) * 0.40 + (montant_imposable - 1805677) * 0.45
    return taxe

# Montant initial
principal = 500000
patrimoine_existant = 500_000  # 1 000 000 € - 100 000 €

# Frais de gestion annuels pour l'AV (0.5%)
frais_gestion_av = 0.0075

# Scénario spécifique : 20 ans avec un rendement de 5%
duree = 40
rendement = 0.05

# Calculer la valeur future pour l'AV avec frais de gestion
vf_av = valeur_future_avec_frais(principal, rendement, frais_gestion_av, duree)

# Calculer les détails des taxes pour l'AV
taxe_av, gain_av, gain_apres_prelevements_av, gain_imposable_av = frais_success_av(principal, vf_av, duree)

# Calculer la valeur future pour le CTO (sans frais de gestion supplémentaires)
vf_cto = valeur_future_avec_frais(principal, rendement, 0, duree)

# Calculer les frais de succession pour le CTO
montant_total_cto = patrimoine_existant + vf_cto
taxe_cto = frais_success_cto(montant_total_cto)

# Calculer le montant net après taxes
net_av = (patrimoine_existant + vf_av) - taxe_av
net_cto = montant_total_cto - taxe_cto

# Afficher les détails pour le scénario spécifique
print("Détail des calculs pour un scénario de 20 ans avec un rendement de 5%:")
print(f"Valeur future de l'investissement en AV: {vf_av:.2f} €")
print(f"Gains en AV: {gain_av:.2f} €")
print(f"Gains après prélèvements sociaux en AV: {gain_apres_prelevements_av:.2f} €")
print(f"Gains imposables en AV après abattement: {gain_imposable_av:.2f} €")
print(f"Taxe sur les successions en AV: {taxe_av:.2f} €")
print(f"Valeur du patrimoine final en AV: {net_av:.2f} €")
print(f"Valeur future de l'investissement en CTO: {vf_cto:.2f} €")
print(f"Taxe sur les successions en CTO: {taxe_cto:.2f} €")
print(f"Valeur du patrimoine final en CTO: {net_cto:.2f} €")

# Calculer la différence relative
difference_relative = (net_cto - net_av) / net_av * 100
print(f"Différence relative CTO vs AV: {difference_relative:.2f}%")
