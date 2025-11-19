"""Générateur de conventions d'avance en compte courant."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


@dataclass(frozen=True)
class PartyInfo:
    """Informations d'une entité signataire de la convention."""

    name: str
    legal_form: str
    share_capital: str
    registration_city: str
    registration_number: str
    address: str
    representative: str
    representative_title: str

    def to_markdown(self) -> str:
        return (
            f"**{self.name}**, {self.legal_form} au capital de {self.share_capital},"
            f" immatriculée au RCS de {self.registration_city} sous le numéro {self.registration_number},"
            f" dont le siège social est situé {self.address}, représentée par {self.representative},"
            f" en qualité de {self.representative_title}."
        )


@dataclass(frozen=True)
class AdvanceTerms:
    """Paramètres décrivant l'avance consentie."""

    purpose: str
    amount: Decimal
    currency: str = "EUR"
    availability_date: date
    repayment_date: date
    interest_rate: Optional[Decimal] = None
    remuneration_description: Optional[str] = None
    repayment_terms: str = "L'avance est remboursable à tout moment à la demande du prêteur."
    termination_conditions: str = (
        "Chacune des parties pourra mettre fin à la présente convention moyennant un préavis de 15 jours par lettre recommandée."
    )
    confidentiality_clause: str = (
        "Les informations échangées dans le cadre de la présente convention sont confidentielles et ne peuvent être divulguées qu'avec l'accord écrit de l'autre partie."
    )
    governing_law: str = "Droit français"


def _format_amount(value: Decimal, currency: str) -> str:
    quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    formatted = f"{quantized:,.2f}".replace(",", " ").replace(".", ",")
    return f"{formatted} {currency}"


def _format_date(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _format_interest(interest_rate: Optional[Decimal], description: Optional[str]) -> str:
    if description:
        return description
    if interest_rate is None:
        return "L'avance est consentie à titre gratuit et ne porte pas intérêt."
    rate = interest_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return (
        "L'avance porte intérêt au taux annuel fixe de "
        f"{rate.normalize()} % calculé sur la base du nombre exact de jours écoulés sur 360 jours."
    )


def generate_current_account_advance_agreement(
    lender: PartyInfo,
    borrower: PartyInfo,
    terms: AdvanceTerms,
    signature_city: str,
    signature_date: date,
) -> str:
    """Produit une convention prête à partager au format Markdown."""

    amount = _format_amount(terms.amount, terms.currency)
    availability_date = _format_date(terms.availability_date)
    repayment_date = _format_date(terms.repayment_date)
    remuneration = _format_interest(terms.interest_rate, terms.remuneration_description)
    signature = _format_date(signature_date)

    lines = ["# Convention d'avance en compte courant", ""]
    lines.append("**Entre les soussignés :**")
    lines.append("- " + lender.to_markdown())
    lines.append("- " + borrower.to_markdown())
    lines.append("")

    lines.append("Collectivement désignés les « Parties » et individuellement une « Partie ».")
    lines.append("")
    lines.append("## Préambule")
    lines.append(
        f"Le prêteur souhaite soutenir la trésorerie de l'emprunteur en mettant à sa disposition une avance en compte courant "
        f"afin de financer {terms.purpose}."
    )
    lines.append(
        "Les Parties se sont rapprochées pour formaliser les conditions de cette avance conformément aux dispositions du Code de commerce."
    )
    lines.append("")

    lines.append("## Article 1 – Objet")
    lines.append(
        f"La présente convention a pour objet de fixer les modalités de l'avance en compte courant consentie par {lender.name}"
        f" au profit de {borrower.name}."
    )
    lines.append("")

    lines.append("## Article 2 – Montant et mise à disposition")
    lines.append(
        f"Le montant maximum de l'avance est fixé à {amount}. Elle sera mise à disposition de l'emprunteur à compter du {availability_date}"
        " par simple transfert sur le compte bancaire habituel."
    )
    lines.append("L'avance est enregistrée en compte courant d'associé et pourra faire l'objet de tirages successifs dans la limite du montant autorisé.")
    lines.append("")

    lines.append("## Article 3 – Rémunération")
    lines.append(remuneration)
    lines.append("")

    lines.append("## Article 4 – Remboursement")
    lines.append(
        f"L'emprunteur remboursera intégralement l'avance au plus tard le {repayment_date}. {terms.repayment_terms}"
    )
    lines.append("Tout remboursement partiel viendra en priorité apurer les intérêts échus avant d'imputer le capital restant dû.")
    lines.append("")

    lines.append("## Article 5 – Déclarations et engagements")
    lines.append(
        f"{borrower.name} s'engage à informer sans délai {lender.name} de tout événement susceptible d'affecter sa capacité à honorer ses engagements."
    )
    lines.append(terms.confidentiality_clause)
    lines.append("")

    lines.append("## Article 6 – Résiliation")
    lines.append(terms.termination_conditions)
    lines.append("En cas de manquement grave par l'une des Parties, l'autre Partie pourra exiger le remboursement immédiat de l'avance.")
    lines.append("")

    lines.append("## Article 7 – Loi applicable et juridiction compétente")
    lines.append(
        f"La présente convention est régie par le {terms.governing_law}. Tout différend relatif à son interprétation ou son exécution sera soumis aux tribunaux compétents du ressort de {signature_city}."
    )
    lines.append("")

    lines.append("## Signatures")
    lines.append(f"Fait à {signature_city}, le {signature}.")
    lines.append("")
    lines.append("Pour le prêteur")
    lines.append("")
    lines.append("Pour l'emprunteur")

    return "\n".join(lines)
