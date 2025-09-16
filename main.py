"""Script principal pour générer une revue comptable à partir d'exports CSV."""

from __future__ import annotations

import argparse
from pathlib import Path
from revue_comptable import generate_accounting_review, read_general_ledger, read_trial_balance


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Génère une revue comptable à partir d'une balance générale et d'un grand livre."
    )
    parser.add_argument(
        "--balance",
        required=True,
        help="Chemin du fichier CSV contenant la balance générale du SPV.",
    )
    parser.add_argument(
        "--grand-livre",
        "--ledger",
        dest="ledger",
        required=True,
        help="Chemin du fichier CSV contenant le grand livre du SPV.",
    )
    parser.add_argument(
        "--sortie",
        "--output",
        dest="output",
        help="Chemin du fichier où stocker la revue générée (Markdown). Si omis, la revue est affichée à l'écran.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    try:
        trial_balance = read_trial_balance(args.balance)
        general_ledger = read_general_ledger(args.ledger)
    except ValueError as exc:
        raise SystemExit(f"Erreur lors de la lecture des fichiers : {exc}") from exc

    report = generate_accounting_review(trial_balance, general_ledger)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report, encoding="utf-8")
        print(f"Revue comptable générée dans {output_path.resolve()}")
    else:
        print(report)


if __name__ == "__main__":
    main()
