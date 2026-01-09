>Ça me rend dingue de voir l'assurance-vie recommandée par pur réflexe à des épargnants de 30 ans, sans jamais questionner la pertinence réelle du support. Pour arrêter de répéter sans cesse les mêmes explications, j'ai compilé ici une démonstration chiffrée prouvant que le Compte Titres (CTO) est, dans l'immense majorité des cas, une solution bien plus performante. Ce post a vocation à servir de référence pour balayer les idées reçues. Il vise aussi à apporter la rigueur qui manque cruellement à certaines ressources populaires sur la succession qui me semble passer à côté de l'essentiel. Ce poste permet aussi de rentrer un peu plus dans le détail de cette vidéo : https://www.youtube.com/watch?v=LMozzlvY8n8&t=1008s

## Sommaire des cas étudiés

Dans ce document, nous analyserons comparativement le CTO et l'AV à travers une série de simulations couvrant :

*   **Impact du profil de risque** : Comparaison pour des rendements de 3% (prudent), 5% (équilibré) et 8% (dynamique).
*   **Stratégies de rente** : Analyse de la consommation de capital à la retraite (cas "FIRE" à 50 ans et cas "Senior" à 65 ans).
*   **Transmission complexe** : Le cas spécifique de l'héritage entre frères et sœurs.
*   **Gestion des imprévus** : L'impact d'un "accident de liquidité" (vente forcée en cours de vie).
*   **Robustesse** : Sensibilité des résultats au turnover (arbitrages fréquents) et simulation d'un portefeuille diversifié réel.

# Mécanismes fiscaux

Les comparaisons proposées ici reposent sur le cadre fiscal actuel (bon celui de 2025 puisque l'ensemble de ces figures ont été rédigées l'année dernière...), c'est à dire avec une flat tax à 31.2% (12.8% impôt sur le revenu + 18.6% prélèvements sociaux), 17.2% de prélèvements sociaux en AV et, un abattement forfaitaire en cas de retrait d'une assurance vie après une certaine période de détention, si la fiscalité venait à changer, le reste de ces simulations deviendrait caduc, ou du moins imprécise.

Le compte titres permet une composition du capital sans frais annuel et efface les plus-values au décès, mais subit une taxation successorale progressive pouvant atteindre 45 %, d'après le barême général des impôts sur les successions. L'Assurance vie impose des frais de gestion annuels qui réduisent le capital, en échange d'un abattement de 152 500 € appliquable après prélèvements sociaux et d'un taux d'imposition un peu plus doux.

Commençons par un exemple : sur 20 ans avec 100 000 € de capital à investir, pour un rendement moyen sur la période de 5 %. Nous supposerons un capital éxistant, dans d'autres actifs (immobiliers, autres support d'investissement, ...), de 500 000 €. Sur un Compte Titres, le capital final atteint 265 330 €. La plus-value latente est effacée au décès et seuls les droits de succession s'appliquent sur la valeur de marché. L'héritier reçoit environ 216 000 € (du CTO). Sur une Assurance vie, le capital final est réduit à 241 171 € par les frais de gestion (qui coûtent tout de même 49 000€ sur la période !). Au décès, les prélèvements sociaux réduisent l'assiette taxable. Après application de l'abattement et de la taxe, l'héritier perçoit 204 000 €. Le compte titres est ici plus favorable car les frais de gestion cumulés sur deux décennies dépassent l'économie fiscale offerte par l'AV.

# Analyse des scénarios

Le cadre de l'étude est celui d'un investissement unique ou en lump sum, réalisé aujourd'hui, dans une optique de transmission en ligne directe (parents vers enfants), sauf mention contraire. Dans tous ces scénarios, un patrimoine existant de 300 000€ est supposé hors de chaque enveloppe.

>Notons dès à présent, que, dans le cas d'une donation du vivant, les résultats seront encore plus intéressants que ceux présentés ci-dessous pour le CTO, puisque dans ce cas, nous utilisons complètement la purge des plus-values latentes mais surtout, l'abattement du barème générale qui est ici en partie consommé par les 300 000€ de capital hors enveloppe spécifique.

Pour uniformiser les résultats et permettre une comparaison équitable, l'ensemble des figures suivantes présentent l'avantage de l'une ou l'autre des enveloppes (CTO vs AV) en **écart relatif par rapport au patrimoine net total transmis** (incluant les actifs hors enveloppe comme l'immobilier ou les livrets, estimés ici à 300 000 €).

La formule utilisée est la suivante :

$$ \text{écart relatif (\%)} = \frac{(\text{héritage hors enveloppe} + \text{AV})_{net} - (\text{héritage hors enveloppe} + \text{CTO})_{net}}{\max\left((\text{héritage hors enveloppe} + \text{AV})_{net}, (\text{héritage hors enveloppe} + \text{CTO})_{net}\right)} \times 100 $$

Ainsi, un écart de +5 % signifie que l'Assurance Vie permet de transmettre 5 % de patrimoine net total en plus que le CTO. À l'inverse, un écart de -5 % signifie que le CTO est supérieur de 5 %.


Nous avons modélisé différents scénarios pour identifier le point de bascule entre les deux enveloppes fiscales. Les graphiques ci-dessous représentent en rouge les zones où le CTO est plus performant, et en vert celles favorables à l'assurance vie.

## Impact du Rendement (Profil de Risque)

L'impact du rendement annuel est déterminant sur la performance relative. Plus le rendement est élevé, plus l'effet "boule de neige" joue en faveur du CTO (qui ne subit pas de frais de gestion sur l'encours), malgré sa fiscalité de sortie potentiellement plus lourde.

### Profil Prudent (3 %)

![Heatmap Profil Prudent](images/heatmap_tipping_point_3pct.png)

Sur un horizon de (10 à 50 ans), l'assurance vie souffre de la comparaison face au compte titres, même lorsque l'abattement successoral est déjà consommé par un patrimoine préexistant (ici 300 000 €). L'avantage ou le désavantage est exprimé en pourcentage du patrimoine net final transmis. La ligne noire indique le point d'équilibre : à gauche (vert), l'Assurance vie l'emporte, à droite (rouge), le CTO devient supérieur. Pour un investissement de 100 000 €, le CTO prend l'avantage vers 15 ans pour un patrimoine modeste, 30 ans pour un patrimoine plus important.

Notons aussi de forte non linéarité due aux taux de taxation lors de l'héritage, l'AV a un abattement de 152 500 € et un taux forfaitaire de 20% entre 152 500€ et 852 500€, puis 31,25 % au delà.

Dans le cas du CTO et du barême général, les taux varient de 20% à 45%, mais les taux d'imposition de la transmission sont comparables pour des patrimoines autour de 500 000€ - 1M€, ce qui donne mécaniquement bien plus d'avantage au CTO qui n'a aucun frais annuel et ne doit pas s'acquitter des prélèvements sociaux (17,2%) sur les plus values.

### Profil Équilibré (5 %)

![Heatmap Profil Équilibré](images/heatmap_tipping_point_5pct.png)

Le constat ici est similaire, l'assurance vie perd son avantage encore plus rapidement, le rendement plus important augmente mécaniquement l'avantage du CTO et de la purge des plus values lors de la transmission, tandis que ce rendement pénalise encore l'assurance vie dont les frais sont proportionnels au capital.

Cependant, on observe que pour les très hauts patrimoine l'assurance vie reste intéressante plus longtemps puisque le taux marginale du barême spécifique est de 31.5% tandis qu'il est de 45% dans le barême général pour les transmissions supérieures à 1 805 677€. Cependant, quoi qu'il arrive, après 25 ans de détention, l'assurance vie est toujours perdante.

### Profil Dynamique (8 %)

![Heatmap Profil Dynamique](images/heatmap_tipping_point.png)

Dans ce scénario à fort rendement, le CTO est pratiquement imbattable. La purge des plus-values latentes au décès neutralise une telle pression fiscale par rapport aux prélèvements sociaux de l'AV que le match est clos avant même 10 ans de détention, sauf pour les patrimoines très élevés dont le taux marginale reste intéressants, dans cas du barème de l'assurance vie par rapport au barême général.

## Stratégies de Consommation (Rente)

Souvent présentée comme l'outil idéal pour la retraite, l'assurance vie est-elle vraiment supérieure lorsqu'il s'agit de consommer son capital ?

### Cas pratique : La rente "FIRE" (Investissement à 50 ans, retraits à 70 ans)

Cette simulation porte sur 100 000 € investis à 50 ans avec retraits annuels de 3 000 € à partir de 70 ans et jusqu'au décès.

![Heatmap scénario rente](images/heatmap_rente.png)

Le résultat confirme la supériorité du CTO sur le long terme dès lors que le rendement dépasse 4%. L'absence de frais de gestion permet de maintenir une base de capital plus élevée, ce qui compense largement la taxation légèrement plus importante des retraits.

### Cas pratique : La rente tardive (Investissement à 65 ans, retraits à 75 ans)

Dans ce scénario, l'épargnant investit plus tardivement et commence ses retraits plus tard, il conserve donc mécaniquement ses différents contrats moins longtemps.

![Heatmap scénario rente senior](images/heatmap_rente_senior.png)

Ici, l'assurance vie montre une résilience plus forte pour les décès avant 85 ans sur des rendements modérés. Cependant, dès que l'horizon s'allonge ou que le rendement est dynamique, le CTO reprend l'avantage grâce à sa structure sans frais et à la purge totale des plus-values latentes au décès sur le reliquat du capital, même si la taxation pour obtenir la rente est légèrement plus lourde.

### Analyse technique : La mécanique des retraits

Pour verser 3 000 € net dans la poche de l'épargnant, il doit vendre, dans l'une ou l'autre des enveloppes, une quantité de capital supérieure afin de couvrir l'impôt. Ce calcul dépend du ratio de plus-value (noté R) présent dans le portefeuille au moment du retrait.

|Mécanique|Compte titres (Flat Tax 31.2 %)|Assurance vie (après 8 ans)\*|
|:-|:-|:-|
|Formule de retrait brut|$3000 / (1 - 0.312 \times R)$|$3000 / (1 - 0.172 \times R)$|
|Exemple (rendement de 100 %)|$R = 0,5$|$R = 0,5$|
|Retrait brut nécessaire|3 555 €|3 282 €|
|Impôt payé|555 € (Flat Tax)|282 € (prélèvements sociaux)|

L'assurance vie bénéficie d'un abattement annuel de 4 600 € sur la part de gains lors des retraits. Pour une rente de 3 000 €, la totalité de la plus-value est absorbée par cet abattement, ce qui ramène l'impôt sur le revenu à 0 %. Seuls les prélèvements sociaux de 17,2 % s'appliquent sur la base des gains, expliquant pourquoi le taux global reste de 17,2 % au lieu de 24,7 %. Ce dernier taux ne s'appliquerait que sur la fraction des gains excédant l'abattement annuel de 4 600 €.

## Situations Particulières

### Transmission Collatérale (Frères et Sœurs)

![Heatmap Frères Soeurs](images/heatmap_siblings_5pct.png)

La transmission entre frères et sœurs constitue une exception notable du fait de la fiscalité punitive de droit commun (35 % puis 45 %). L'assurance vie offre un avantage bien plus large pour les capitaux modestes ou les durées raisonnables. Cependant, le Compte Titres finit par l'emporter à long terme sous l'effet des frais : le point de bascule se situe autour de 25 ans pour les patrimoines importants (plus d'un million d'euros) mais recule au-delà de 50 ans pour les capitaux plus modestes (100 000 €).

### Analyse : L'érosion par les frais sur les gros patrimoines

Contrairement à la ligne directe, le taux marginal de 45 % est atteint très vite pour les frères et sœurs (dès 24 430 €). L'avantage fiscal de l'AV se stabilise donc rapidement (31,25 % max contre 45 % en CTO). Dès lors, les frais de gestion de 0,5 % par an finissent par peser bien plus lourd que l'économie d'impôt.

**Illustration pour 10 000 000 € (30 ans, rendement 5 %)** :

* Héritage Net CTO : 23 780 229 € (Taxé à 45 %, mais 0 frais avant)
* Héritage Net AV : 22 629 130 € (Taxé à 31,25 %, mais après 5,7 M€ de frais)
* Avantage Net CTO : +1 151 099 €

Ici, les frais de gestion (5,7 M€) ont littéralement dévoré l'avantage fiscal de l'AV. Plus le patrimoine est élevé, plus l'assurance vie devient inefficace.

Finalement, et de manière assez surprenante, même dans ce cas, l'assurance vie n'est pas nécessairement à recommander chez des profils jeunes. Ou des profils plus agés, mais très fortunés.

### Gestion des Imprévus : L'accident de liquidité

Ce scénario étudie l'impact d'une vente forcée intervenant en cours de vie du placement, par exemple suite à la fermeture d'un ETF.

![Heatmap Accident](images/heatmap_accident.png)

L'assurance vie offre ici une protection majeure. En compte titres, la vente déclenche immédiatement l'imposition des plus-values (31.2 %). Cette ponction fiscale ampute le capital, qui cesse de produire des intérêts composés sur la somme versée à l'État. En assurance vie, l'arbitrage est fiscalement neutre tant que l'argent ne sort pas de l'enveloppe.

La carte illustre cette supériorité quasi-totale de l'assurance vie. Plus le rendement est élevé et plus l'accident survient tardivement dans la vie de l'épargnant, plus le coût d'opportunité de l'impôt anticipé en compte titres est dévastateur.

## Analyse de la Robustesse

### Sensibilité au Turnover (Rotations de portefeuille)

La supériorité du CTO repose en grande partie sur la purge des plus-values au décès, nous avons déjà vu qu'une vente forcée est très négative pour cette enveloppe. Ici, nous allons étudier jusqu'à quel niveau de rotation (proportion du capital vendu/acheté par an), l'avantage du CTO persiste.

![Comparaison Stochastique : Rendement vs Turnover](images/stochastic_dual_scenario.png)

Ce graphique compare la probabilité de réussite du CTO face à l'AV selon le taux de rotation annuel (axe Y) et le rendement espéré (axe X) dans deux contextes successoraux. Le taux de rotation (ou turnover) correspond à la part du portefeuille qui est liquidée et rachetée chaque année. Cela peut représenter :

* Des reventes forcées (fermeture d'un ETF par son émetteur).
* Des arbitrages entre différents actifs (ex: actions vers obligations).
* Un changement de stratégie ou de gérant.

Dans le cas où l'investisseur possède déjà un patrimoine de 300 000 € (hors CTO/AV), on observe que pour des taux de rotation inférieurs à 5 %, le CTO domine presque toujours. Au-delà de ce seuil, l'assurance vie commence à regagner du terrain grâce à son enveloppe fiscale interne qui protège les arbitrages contre la flat tax. En revanche, si l'abattement du régime général n'est pas consommé (0 € de patrimoine préexistant), le CTO reste supérieur même avec une rotation élevée du portefeuille.

### Cas Concret : Portefeuille diversifié (NTSG, Managed Futures, Or)

Pour illustrer cette robustesse, nous avons simulé une stratégie diversifiée composée de 80 % de NTSG (fonds multi-actifs, 90% actions et 60% obligations), 10 % de Managed futures et 10 % d'or.

![Résultats portefeuille complexe](images/complex_portfolio_results.png)

Bien que cette stratégie nécessite un rééquilibrage annuel entre les trois actifs (générant un turnover moyen de 2,44 %), le CTO l'emporte dans 84,4 % des cas à 30 ans. Le coût fiscal des arbitrages en CTO est largement compensé par l'économie des 0,5 % de frais de gestion de l'assurance vie et par la purge totale des plus-values lors de la succession.

### Dynamique Temporelle de l'Avantage Fiscal

Une autre analyse, modifiant la durée de détention des deux enveloppes, montre que l'avantage du CTO croît avec le temps avant de se stabiliser, car les frais de l'AV s'appliquent sur un capital de plus en plus massif, mais les plus values, générant des taxes dans le CTO s'accumulent aussi, finissant par dépasser les frais annuels de l'assurance vie.

| Durée | Médiane CTO | Médiane AV | Avantage CTO (€) | Avantage Relatif (%) | Prob. Victoire CTO |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 20 ans | 307 434 € | 294 407 € | **+13 027 €** | **+2.29 %** | 73,0 % |
| 30 ans | 563 804 € | 538 977 € | **+24 827 €** | **+3.01 %** | 84,4 % |
| 40 ans | 1 019 056 € | 989 926 € | **+29 130 €** | **+2.27 %** | 72,2 % |
| 50 ans | 1 799 757 € | 1 794 266 € | **+5 491 €** | **+0.27 %** | 54,1 % |
| 60 ans | 3 254 123 € | 3 316 243 € | **-62 120 €** | **-1.74 %** | 37,3 % |
| 70 ans | 6 248 248 € | 6 429 552 € | **-181 304 €** | **-2.71 %** | 23,8 % |

L'avantage du CTO finit par s'inverser entre 50 et 60 ans. À ces horizons, la fiscalité des arbitrages annuels (taxés à 30 % sur la plus value dans le CTO) finit par éroder la capitalisation plus lourdement que les 0,5 % de frais de gestion de l'assurance vie. Toutefois, ce modèle suppose un capital fermé, et unique, investit en lump sum. En pratique, un épargnant effectuant des versements réguliers (DCA) peut rééquilibrer son portefeuille sans vendre ses actifs gagnants, simplement en orientant sa nouvelle épargne vers les actifs sous-pondérés. Cette stratégie de rééquilibrage éliminerait la friction fiscale du CTO. Ainsi, les résultats de cette simulation particulièrement conservateurs pour le Compte Titres.

# Conclusion

Un compte titres sans frais est la solution par défaut la plus performante pour la majorité des épargnants sur le long terme, même si des questions de rééquilibrage entre en jeux. L'assurance vie est un outil d'optimisation spécifique pour les transmissions en ligne indirecte sur des durées courtes, autrement dit, si, malheureusement, l'espérance de vie au moment de la souscription est courte. Rappelons par ailleurs, que le cadre fiscal utilisé dans ce post, ne concerne que les versements effectués avant 70 ans. Dans tous les cas, une détention supérieure à 30 ans favorise presque toujours le compte titres. Ainsi, si vous avez moins de 60 ans, même le meilleur contrat d'assurance vie sera mécaniquement perdant pour vous, n'y investissez rien.