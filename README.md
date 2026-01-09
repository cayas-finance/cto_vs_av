<img src="Logo & icons Cayas/Logo & icons Cayas/logo cayas/png/white/logo-cayas-HD-1920-white.png" alt="Logo Cayas">
https://app.cayas.fr

Ce dépôt compare le CTO (Compte Titres) et l’AV (Assurance Vie) via plusieurs scénarios, avec une UI disponible dans votre navigateur et des simulations Python pour reproduire les images disponibles dans le post original. 

Notons ici que ces figures diffèrent, actuellement, légèrement de celles du post, la raison est que j'ai ajouté les frais de notaire lors de la transmission d'un CTO, ce coût était initialement négligée. Je mets le post à jour dès que nous avons bien compris les frais et les conditions pour lesquels ils s'appliquent. Pour l'heure, nous appliquons uniquement le barème forfaitaire, il s'agit d'une approximation des frais réels. 

## Structure
- `ui/` interface statique (ouvrir `ui/index.html` ou servir le dossier) et logique dans `ui/simulate.js`
- `api/` service FastAPI pour les tests de parité et scénarios
- `cto_av_comp/` modèle et helpers de simulation
- `simulations/` scripts qui génèrent les figures dans `images/`

## Installation
Créer un virtualenv et installer les dépendances :
```
make install-venv
make install-deps
source .venv/bin/activate
```

## Lancer l’API
```
make api
```
Port par défaut : 8001.

## Lancer les simulations
```
make simulations
```
Cela exécute tous les scripts de `simulations/`, génère les images dans `images/`.

## Notes / hypothèses
- Le rendement est modélisé en brut, avant frais d’enveloppe et fiscalité.
- Le CTO est en buy & hold par défaut ; la rotation applique la flat tax sur les plus-values réalisées.
- Les retraits AV après 8 ans appliquent l’abattement annuel et les seuils d’IR réduits.
- La succession AV applique les prélèvements sociaux sur les gains au décès.
