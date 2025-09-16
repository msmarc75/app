"""Fonctions utilitaires pour importer des fichiers comptables au format CSV."""

from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

from .model import LedgerEntry, TrialBalanceEntry

# Formats de dates couramment rencontrés dans les exports comptables.
_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%Y/%m/%d",
    "%d/%m/%y",
    "%d-%m-%y",
    "%Y%m%d",
)


def _normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "").replace("_", "").replace("-", "")


_TRIAL_BALANCE_COLUMNS: Mapping[str, Iterable[str]] = {
    "account": ("account", "compte", "numero", "numéro", "no", "ncompte"),
    "label": ("label", "intitule", "intitulé", "libelle", "libellé", "description"),
    "debit": ("debit", "deb", "montantdebit", "debitmontant", "débit", "md"),
    "credit": ("credit", "cred", "montantcredit", "creditmontant", "crédit", "mc"),
}


_LEDGER_REQUIRED_COLUMNS: Mapping[str, Iterable[str]] = {
    "date": ("date", "dateecriture", "datedecriture", "valuedate"),
    "account": ("account", "compte", "numero", "numéro"),
    "label": ("label", "intitule", "intitulé", "libelle", "libellé", "intitulesecondaire"),
    "description": ("description", "memo", "detail", "libellepiece", "commentaire", "piece"),
    "debit": ("debit", "deb", "montantdebit", "débit", "md"),
    "credit": ("credit", "cred", "montantcredit", "crédit", "mc"),
}


_LEDGER_OPTIONAL_COLUMNS: Mapping[str, Iterable[str]] = {
    "journal": ("journal", "codejournal"),
    "reference": ("reference", "piece", "numreference", "numpiece"),
}


def _build_column_map(
    fieldnames: Iterable[str],
    required: Mapping[str, Iterable[str]],
    optional: Optional[Mapping[str, Iterable[str]]] = None,
) -> Dict[str, str]:
    normalized = {_normalize_header(name): name for name in fieldnames if name}
    resolved: Dict[str, str] = {}

    for canonical, candidates in required.items():
        found = None
        for candidate in candidates:
            key = _normalize_header(candidate)
            if key in normalized:
                found = normalized[key]
                break
        if not found:
            raise ValueError(
                f"Impossible de repérer la colonne obligatoire « {canonical} » dans le fichier."
            )
        resolved[canonical] = found

    if optional:
        for canonical, candidates in optional.items():
            for candidate in candidates:
                key = _normalize_header(candidate)
                if key in normalized:
                    resolved[canonical] = normalized[key]
                    break

    return resolved


def _parse_decimal(raw_value: str) -> Decimal:
    value = raw_value.strip()
    if not value:
        return Decimal("0")

    negative = False
    if value.startswith("(") and value.endswith(")"):
        negative = True
        value = value[1:-1]
    if value.startswith("-"):
        negative = True
        value = value[1:]
    elif value.startswith("+"):
        value = value[1:]

    # Nettoyage des séparateurs de milliers courants.
    for sep in ("\u202f", "\xa0", " "):
        value = value.replace(sep, "")

    if value.count(",") == 1 and value.count(".") == 0:
        value = value.replace(",", ".")
    elif value.count(",") > 1 and value.count(".") == 0:
        value = value.replace(",", "")
    elif value.count(".") > 1 and value.count(",") == 0:
        value = value.replace(".", "")
    elif value.count(",") == 1 and value.count(".") == 1:
        # On considère que le séparateur décimal est le dernier signe utilisé.
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")

    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Valeur numérique invalide: {raw_value!r}") from exc

    return -amount if negative else amount


def _parse_date(value: str) -> datetime.date:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Date manquante")
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Format de date inconnu: {value!r}")


def read_trial_balance(path: Path | str) -> List[TrialBalanceEntry]:
    """Charge une balance générale exportée au format CSV."""

    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("Le fichier de balance générale ne contient pas d'en-têtes.")
        columns = _build_column_map(reader.fieldnames, _TRIAL_BALANCE_COLUMNS)

        entries: List[TrialBalanceEntry] = []
        for lineno, row in enumerate(reader, start=2):
            account = row.get(columns["account"], "").strip()
            if not account:
                # Ligne vide ou commentaire
                continue
            label = row.get(columns["label"], "").strip()
            try:
                debit = _parse_decimal(row.get(columns["debit"], "0"))
                credit = _parse_decimal(row.get(columns["credit"], "0"))
            except ValueError as exc:
                raise ValueError(
                    f"Impossible d'interpréter les montants de la ligne {lineno}: {exc}"
                ) from exc

            entries.append(TrialBalanceEntry(account=account, label=label, debit=debit, credit=credit))

    if not entries:
        raise ValueError("Aucune ligne valide trouvée dans la balance générale.")

    return entries


def read_general_ledger(path: Path | str) -> List[LedgerEntry]:
    """Charge un grand livre exporté au format CSV."""

    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("Le fichier de grand livre ne contient pas d'en-têtes.")
        columns = _build_column_map(
            reader.fieldnames, _LEDGER_REQUIRED_COLUMNS, optional=_LEDGER_OPTIONAL_COLUMNS
        )

        entries: List[LedgerEntry] = []
        for lineno, row in enumerate(reader, start=2):
            account = row.get(columns["account"], "").strip()
            if not account:
                continue
            try:
                entry_date = _parse_date(row.get(columns["date"], ""))
            except ValueError as exc:
                raise ValueError(
                    f"Impossible d'interpréter la date à la ligne {lineno}: {exc}"
                ) from exc

            label = row.get(columns["label"], "").strip()
            description = row.get(columns["description"], "").strip()
            try:
                debit = _parse_decimal(row.get(columns["debit"], "0"))
                credit = _parse_decimal(row.get(columns["credit"], "0"))
            except ValueError as exc:
                raise ValueError(
                    f"Impossible d'interpréter les montants de la ligne {lineno}: {exc}"
                ) from exc

            journal = row.get(columns.get("journal", ""), "").strip() if "journal" in columns else None
            reference = (
                row.get(columns.get("reference", ""), "").strip() if "reference" in columns else None
            )

            entries.append(
                LedgerEntry(
                    date=entry_date,
                    account=account,
                    label=label,
                    description=description,
                    debit=debit,
                    credit=credit,
                    journal=journal or None,
                    reference=reference or None,
                )
            )

    if not entries:
        raise ValueError("Aucune ligne valide trouvée dans le grand livre.")

    return entries
