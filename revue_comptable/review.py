"""Génération d'une revue comptable synthétique."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, List, Sequence, Tuple

from .model import LedgerEntry, TrialBalanceEntry


@dataclass
class _AccountAggregate:
    label: str
    debit: Decimal
    credit: Decimal

    @property
    def balance(self) -> Decimal:
        return self.debit - self.credit


_TOLERANCE = Decimal("0.01")
_SIGNIFICANT_THRESHOLD = Decimal("1.00")


def _format_amount(value: Decimal) -> str:
    quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    formatted = f"{quantized:,.2f}"
    return formatted.replace(",", " ").replace(".", ",")


def _aggregate_trial_balance(entries: Iterable[TrialBalanceEntry]) -> Dict[str, _AccountAggregate]:
    aggregates: Dict[str, _AccountAggregate] = {}
    for entry in entries:
        account = entry.account
        current = aggregates.get(account)
        if current:
            current.debit += entry.debit
            current.credit += entry.credit
            if not current.label and entry.label:
                current.label = entry.label
        else:
            aggregates[account] = _AccountAggregate(label=entry.label, debit=entry.debit, credit=entry.credit)
    return aggregates


def _aggregate_ledger(entries: Iterable[LedgerEntry]) -> Dict[str, _AccountAggregate]:
    aggregates: Dict[str, _AccountAggregate] = {}
    for entry in entries:
        account = entry.account
        current = aggregates.get(account)
        if current:
            current.debit += entry.debit
            current.credit += entry.credit
            if not current.label and entry.label:
                current.label = entry.label
        else:
            aggregates[account] = _AccountAggregate(label=entry.label, debit=entry.debit, credit=entry.credit)
    return aggregates


def _markdown_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    if not rows:
        return "_Aucune donnée disponible._"
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_rows = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_row, separator_row, *body_rows])


def generate_accounting_review(
    trial_balance: Sequence[TrialBalanceEntry],
    general_ledger: Sequence[LedgerEntry],
) -> str:
    """Produit une revue comptable prête à partager."""

    tb_aggregates = _aggregate_trial_balance(trial_balance)
    gl_aggregates = _aggregate_ledger(general_ledger)

    total_tb_debit = sum((entry.debit for entry in trial_balance), Decimal())
    total_tb_credit = sum((entry.credit for entry in trial_balance), Decimal())
    total_gl_debit = sum((entry.debit for entry in general_ledger), Decimal())
    total_gl_credit = sum((entry.credit for entry in general_ledger), Decimal())

    report_lines: List[str] = ["# Revue comptable du SPV", ""]
    report_lines.append("## Synthèse")
    report_lines.append(
        f"- Total débit balance générale : {_format_amount(total_tb_debit)}"
    )
    report_lines.append(
        f"- Total crédit balance générale : {_format_amount(total_tb_credit)}"
    )
    report_lines.append(
        f"- Écart balance générale : {_format_amount(total_tb_debit - total_tb_credit)}"
    )
    report_lines.append(
        f"- Total débit grand livre : {_format_amount(total_gl_debit)}"
    )
    report_lines.append(
        f"- Total crédit grand livre : {_format_amount(total_gl_credit)}"
    )
    report_lines.append(f"- Écart grand livre : {_format_amount(total_gl_debit - total_gl_credit)}")
    report_lines.append(
        f"- Nombre de comptes dans la balance : {len(tb_aggregates)}"
    )
    report_lines.append(
        f"- Nombre de comptes dans le grand livre : {len(gl_aggregates)}"
    )
    report_lines.append("")

    controls: List[str] = []
    if (total_tb_debit - total_tb_credit).copy_abs() <= _TOLERANCE:
        controls.append("✅ Balance générale équilibrée")
    else:
        controls.append(
            "⚠️ La balance générale n'est pas équilibrée (écart supérieur au seuil toléré)."
        )

    if (total_gl_debit - total_gl_credit).copy_abs() <= _TOLERANCE:
        controls.append("✅ Grand livre équilibré")
    else:
        controls.append(
            "⚠️ Le grand livre présente un déséquilibre (débit ≠ crédit)."
        )

    balance_vs_ledger_diff = (total_tb_debit - total_tb_credit) - (total_gl_debit - total_gl_credit)
    if balance_vs_ledger_diff.copy_abs() <= _TOLERANCE:
        controls.append("✅ Cohérence globale balance / grand livre")
    else:
        controls.append(
            "⚠️ Les soldes globaux de la balance et du grand livre diffèrent."
            " Vérifiez les périodes et les filtres d'export."
        )

    report_lines.append("## Contrôles automatiques")
    for item in controls:
        report_lines.append(f"- {item}")
    report_lines.append("")

    mismatches: List[Tuple[str, _AccountAggregate, _AccountAggregate, Decimal]] = []
    missing_in_ledger: List[Tuple[str, _AccountAggregate]] = []
    missing_in_balance: List[Tuple[str, _AccountAggregate]] = []

    all_accounts = sorted(set(tb_aggregates.keys()) | set(gl_aggregates.keys()))
    for account in all_accounts:
        tb_data = tb_aggregates.get(account)
        gl_data = gl_aggregates.get(account)
        if tb_data and not gl_data:
            missing_in_ledger.append((account, tb_data))
            continue
        if gl_data and not tb_data:
            missing_in_balance.append((account, gl_data))
            continue
        if not tb_data or not gl_data:
            continue
        diff = gl_data.balance - tb_data.balance
        if diff.copy_abs() > _TOLERANCE:
            mismatches.append((account, tb_data, gl_data, diff))

    significant_mismatches = [item for item in mismatches if item[3].copy_abs() >= _SIGNIFICANT_THRESHOLD]

    report_lines.append("## Concordance balance / grand livre")
    if not mismatches:
        report_lines.append("Aucune différence détectée entre la balance et le grand livre.")
    else:
        rows = []
        for account, tb_data, gl_data, diff in mismatches:
            rows.append(
                (
                    account,
                    tb_data.label or gl_data.label or "",
                    _format_amount(tb_data.balance),
                    _format_amount(gl_data.balance),
                    _format_amount(diff),
                )
            )
        report_lines.append(
            _markdown_table(
                ["Compte", "Intitulé", "Solde balance", "Solde grand livre", "Écart"],
                rows,
            )
        )
    if missing_in_ledger:
        report_lines.append("")
        report_lines.append("Comptes absents du grand livre :")
        rows = [
            (
                account,
                data.label,
                _format_amount(data.balance),
            )
            for account, data in missing_in_ledger
        ]
        report_lines.append(
            _markdown_table(["Compte", "Intitulé", "Solde balance"], rows)
        )
    if missing_in_balance:
        report_lines.append("")
        report_lines.append("Comptes absents de la balance générale :")
        rows = [
            (
                account,
                data.label,
                _format_amount(data.balance),
            )
            for account, data in missing_in_balance
        ]
        report_lines.append(
            _markdown_table(["Compte", "Intitulé", "Solde grand livre"], rows)
        )
    report_lines.append("")

    if significant_mismatches:
        report_lines.append("### Écarts significatifs")
        rows = [
            (
                account,
                tb.label or gl.label,
                _format_amount(diff),
            )
            for account, tb, gl, diff in significant_mismatches
        ]
        report_lines.append(
            _markdown_table(["Compte", "Intitulé", "Écart"], rows)
        )
        report_lines.append("")

    monthly_totals: Dict[str, Tuple[Decimal, Decimal]] = {}
    for entry in general_ledger:
        key = entry.date.strftime("%Y-%m")
        debit, credit = monthly_totals.get(key, (Decimal(), Decimal()))
        monthly_totals[key] = (debit + entry.debit, credit + entry.credit)

    report_lines.append("## Activité mensuelle du grand livre")
    if not monthly_totals:
        report_lines.append("_Aucune écriture trouvée dans le grand livre._")
    else:
        rows = []
        for month in sorted(monthly_totals.keys()):
            debit, credit = monthly_totals[month]
            rows.append(
                (
                    month,
                    _format_amount(debit),
                    _format_amount(credit),
                    _format_amount(debit - credit),
                )
            )
        report_lines.append(
            _markdown_table(["Mois", "Débit", "Crédit", "Solde"], rows)
        )
    report_lines.append("")

    top_entries = sorted(general_ledger, key=lambda entry: entry.amount.copy_abs(), reverse=True)[:5]
    report_lines.append("## Écritures les plus significatives")
    if not top_entries:
        report_lines.append("_Grand livre vide._")
    else:
        rows = []
        for entry in top_entries:
            rows.append(
                (
                    entry.date.strftime("%d/%m/%Y"),
                    entry.account,
                    entry.label,
                    entry.description,
                    _format_amount(entry.debit),
                    _format_amount(entry.credit),
                )
            )
        report_lines.append(
            _markdown_table(
                ["Date", "Compte", "Libellé", "Description", "Débit", "Crédit"], rows
            )
        )
    report_lines.append("")

    if significant_mismatches:
        report_lines.append("## Recommandations")
        report_lines.append(
            "- Analyser les comptes listés dans les écarts significatifs pour identifier les écritures manquantes ou mal ventilées."
        )
        report_lines.append(
            "- Vérifier les exports sources (période, filtres, devise) afin de comprendre les divergences observées."
        )
        report_lines.append(
            "- Documenter les ajustements nécessaires et préparer les écritures de correction avant clôture."
        )
    else:
        report_lines.append("## Conclusion")
        report_lines.append(
            "Les contrôles effectués n'ont pas mis en évidence d'anomalies majeures entre la balance générale et le grand livre."
        )

    return "\n".join(report_lines)
