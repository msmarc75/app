"""Structures de données utilisées par le générateur de revue comptable."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class TrialBalanceEntry:
    """Ligne d'une balance générale."""

    account: str
    label: str
    debit: Decimal
    credit: Decimal

    @property
    def balance(self) -> Decimal:
        """Retourne le solde débiteur (positif) ou créditeur (négatif)."""

        return self.debit - self.credit


@dataclass(frozen=True)
class LedgerEntry:
    """Écriture comptable du grand livre."""

    date: date
    account: str
    label: str
    description: str
    debit: Decimal
    credit: Decimal
    journal: Optional[str] = None
    reference: Optional[str] = None

    @property
    def amount(self) -> Decimal:
        """Retourne le montant signé de l'écriture."""

        return self.debit - self.credit
