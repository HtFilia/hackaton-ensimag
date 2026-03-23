"""Lance les tests publics pour une équipe et écrit les résultats en JSON.

Usage :
    python3 -m src.student.runner --team mon_equipe
    python3 -m src.student.runner --team mon_equipe --output frontend/public/student-results.json
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from src.validation.runner import validate_level_verbose

LEVELS = list(range(1, 7))


def run_student_tests(team: str, output_path: Path) -> None:
    print(f"\n  Notation de l'équipe \033[1m{team}\033[0m — tests publics uniquement\n")

    # Préserver les first_pass_times existants entre les exécutions
    existing: dict = {}
    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text())
        except Exception:
            pass

    first_pass_times: dict = dict(existing.get("first_pass_times", {}))
    now_iso = datetime.now().isoformat(timespec="seconds")

    level_results: dict = {}

    for level_num in LEVELS:
        level_key = f"level{level_num}"
        fixtures = sorted(Path(f"tests/fixtures/{level_key}").glob("*.yaml"))

        if not fixtures:
            level_results[level_key] = {
                "status": "not_tested",
                "duration_ms": 0,
                "fixtures": [],
            }
            continue

        fixture_results = []
        all_passed = True
        total_ms = 0

        for fixture in fixtures:
            t0 = time.perf_counter()
            try:
                res = validate_level_verbose(team, level_key, fixture)
            except Exception as exc:
                res = {"passed": False, "message": f"Erreur inattendue : {exc}", "expected": None, "got": None}
            duration_ms = int((time.perf_counter() - t0) * 1000)
            total_ms += duration_ms

            fixture_results.append({
                "fixture": fixture.name,
                "passed": res["passed"],
                "message": res["message"],
                "duration_ms": duration_ms,
                "expected": res.get("expected"),
                "got": res.get("got"),
            })
            if not res["passed"]:
                all_passed = False

        status = "passed" if all_passed else "failed"
        level_results[level_key] = {
            "status": status,
            "duration_ms": total_ms,
            "fixtures": fixture_results,
        }

        # Enregistrer le premier passage (jamais écraser)
        if all_passed and level_key not in first_pass_times:
            first_pass_times[level_key] = now_iso

        icon = "\033[32m✓\033[0m" if all_passed else "\033[31m✗\033[0m"
        print(f"  {icon}  Palier {level_num} : {status} ({total_ms}ms)")

    passed_count = sum(1 for v in level_results.values() if v["status"] == "passed")
    print(f"\n  Résultat : {passed_count}/6 paliers réussis")

    output = {
        "team": team,
        "updated_at": now_iso,
        "first_pass_times": first_pass_times,
        "levels": level_results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"  Résultats écrits dans \033[36m{output_path}\033[0m\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dashboard étudiant — notation des paliers publics"
    )
    parser.add_argument("--team", required=True, help="Nom du répertoire de soumission")
    parser.add_argument(
        "--output",
        default="frontend/public/student-results.json",
        help="Chemin de sortie JSON (défaut : frontend/public/student-results.json)",
    )
    args = parser.parse_args()
    run_student_tests(team=args.team, output_path=Path(args.output))


if __name__ == "__main__":
    main()
