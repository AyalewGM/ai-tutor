"""Export authored learn_content to a reviewable Markdown document.

Generates one section per concept unit with skill codes it applies to, so a
non-engineer (e.g. a math educator) can review tone, accuracy, and level fit.

    docker compose exec tutor-api python /app/scripts/ops/export_learn_content.py > docs/learn-content-review.md
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Curriculum, Skill


def main() -> None:
    with SessionLocal() as db:
        rows = db.execute(
            select(Skill, Curriculum.code)
            .join(Curriculum, Curriculum.id == Skill.curriculum_id)
            .where(Skill.learn_content.is_not(None))
            .order_by(Skill.code, Curriculum.code)
        ).all()

    # Group skills sharing identical content into one reviewable unit.
    units: dict[int, dict] = {}
    applied: dict[int, list[str]] = {}
    for skill, curriculum_code in rows:
        content = skill.learn_content
        # summary text is a stable identity for a shared concept unit
        key = hash(content.get("summary"))
        units[key] = content
        applied.setdefault(key, []).append(f"{skill.code} ({curriculum_code})")

    print("# Learn-content review\n")
    print("Authored pre-practice instruction shown to learners. Review for")
    print("mathematical accuracy, age-appropriate tone, and terminology.\n")
    for i, (key, content) in enumerate(sorted(units.items(), key=lambda kv: kv[0]), 1):
        print(f"\n---\n\n## Unit {i}")
        print(f"\n**Applies to:** {', '.join(sorted(applied[key]))}\n")
        print(f"**Summary:** {content['summary']}\n")
        for j, example in enumerate(content.get("examples", []), 1):
            print(f"**Example {j}: {example['title']}**")
            for step in example.get("steps", []):
                print(f"  {step}")
            if example.get("answer"):
                print(f"  **Answer: {example['answer']}**")
            print()
        if content.get("key_terms"):
            print("**Key words**")
            for item in content["key_terms"]:
                print(f"- *{item['term']}* — {item['definition']}")
            print()
        if content.get("watch_out"):
            print("**Watch out for**")
            for item in content["watch_out"]:
                print(f"- {item}")
            print()


if __name__ == "__main__":
    main()
