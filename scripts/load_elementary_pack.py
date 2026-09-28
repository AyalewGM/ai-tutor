import argparse
from pathlib import Path

from app.core.database import SessionLocal
from app.elementary_pack import load_pack, parse_pack


def main() -> None:
    parser = argparse.ArgumentParser(description="Load a validated elementary curriculum pack")
    parser.add_argument("pack", type=Path)
    args = parser.parse_args()
    pack = parse_pack(args.pack)
    with SessionLocal() as session:
        result = load_pack(session, pack)
        session.commit()
    print(
        f"Loaded {pack.curriculum.code} {pack.curriculum.version}: "
        f"{result.skill_count} skills, {result.expectation_count} expectations, "
        f"{result.problem_count} problems"
    )


if __name__ == "__main__":
    main()
