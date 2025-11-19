# Générateur de revue comptable pour SPV

Ce projet propose un utilitaire en ligne de commande permettant d'importer une **balance générale** et un **grand livre** d'un véhicule ad hoc (SPV) afin de produire automatiquement une revue comptable documentée.

## Fonctionnalités

- Lecture d'exports CSV issus de la balance générale et du grand livre.
- Identification des déséquilibres et contrôles de cohérence (totaux débit/crédit, concordance balance \<\> grand livre).
- Repérage des comptes absents d'un fichier par rapport à l'autre et des écarts significatifs de solde.
- Synthèse de l'activité mensuelle et liste des écritures les plus significatives.
- Génération d'un rapport au format Markdown prêt à être partagé.
- Création d'une convention d'avance en compte courant personnalisable.

## Formats attendus

Les fichiers doivent être encodés en UTF-8 et contenir une ligne d'en-têtes. Les séparateurs décimaux `,`, `.` ou les parenthèses pour les montants négatifs sont pris en charge. Les colonnes obligatoires sont :

### Balance générale

- Numéro de compte (`compte`, `account`, `numero`, ...)
- Libellé du compte (`libellé`, `label`, ...)
- Montants débit et crédit

### Grand livre

- Date d'écriture (formats usuels : `YYYY-MM-DD`, `DD/MM/YYYY`, `YYYYMMDD`, ...)
- Numéro de compte
- Libellé du compte ou de la contrepartie
- Description / libellé de l'écriture
- Montants débit et crédit
- (Optionnel) Journal, référence de pièce

## Installation

Aucune dépendance externe n'est nécessaire. Le projet fonctionne avec **Python 3.10** ou supérieur.

## Utilisation

```bash
python main.py --balance chemin/vers/balance_generale.csv --ledger chemin/vers/grand_livre.csv --output revue.md
```

Si l'option `--output` est omise, le rapport est affiché directement dans la console.

## Exemple

Des fichiers d'exemple sont fournis dans le dossier [`examples`](examples) :

```bash
python main.py --balance examples/balance_generale.csv --ledger examples/grand_livre.csv --output revue_exemple.md
```

Le fichier `revue_exemple.md` contiendra une revue comptable synthétique basée sur les données d'exemple.

## Générateur de convention d'avance en compte courant

Le paquet expose également un utilitaire pour rédiger automatiquement une convention d'avance en compte courant entre deux parties.
Il suffit de décrire chacune des sociétés signataires et les principales caractéristiques de l'avance.

```python
from datetime import date
from decimal import Decimal

from revue_comptable import (
    AdvanceTerms,
    PartyInfo,
    generate_current_account_advance_agreement,
)

lender = PartyInfo(
    name="Holding Invest",
    legal_form="SAS",
    share_capital="1 000 000 EUR",
    registration_city="Paris",
    registration_number="799 999 999",
    address="10 avenue de l'Europe, 75008 Paris",
    representative="Marie Martin",
    representative_title="Présidente",
)

borrower = PartyInfo(
    name="Projet Solaire 5",
    legal_form="SASU",
    share_capital="10 000 EUR",
    registration_city="Nanterre",
    registration_number="910 000 111",
    address="22 rue des Fleurs, 92000 Nanterre",
    representative="Julien Petit",
    representative_title="Président",
)

terms = AdvanceTerms(
    purpose="le financement du besoin en fonds de roulement",
    amount=Decimal("250000"),
    interest_rate=Decimal("3.5"),
    availability_date=date(2024, 1, 15),
    repayment_date=date(2024, 12, 31),
    remuneration_description="Les intérêts sont calculés au taux annuel fixe de 3,5 % sur la base des jours exacts/360.",
)

agreement = generate_current_account_advance_agreement(
    lender=lender,
    borrower=borrower,
    terms=terms,
    signature_city="Paris",
    signature_date=date(2024, 1, 10),
)

print(agreement)
```

Le texte généré est fourni au format Markdown et peut être envoyé tel quel aux parties prenantes ou inséré dans un modèle bureautique.

## Limites connues

- Les formats propriétaires (Excel, PDF) doivent être exportés en CSV avant import.
- Les écarts inférieurs à 1 EUR sont considérés comme non significatifs dans la synthèse.
- Les contrôles sont réalisés sur la période couverte par les fichiers fournis : veillez à exporter la même plage de dates pour la balance et le grand livre.

## Licence

Ce code est fourni tel quel, sans garantie. Vous pouvez l'adapter librement à vos besoins internes.
