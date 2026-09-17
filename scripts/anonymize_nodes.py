"""Anonymize RAN node names consistently across local project artifacts.

The private mapping is written to node_mapping_private.csv and must not be committed.
Cell IDs are intentionally left unchanged.
"""

from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "node_mapping_private.csv"
DB = ROOT / "reclamations.db"
NODE_RE = re.compile(r"\bB5G4G_[A-Za-z0-9_]+\b")
TEXT_SUFFIXES = {".csv", ".json", ".md", ".tex", ".txt", ".ipynb", ".frm", ".lot"}
NODE_COLUMNS = {"Node", "node_retenu", "vrai_node"}


def read_text(path: Path) -> str | None:
    for encoding in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return None


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def collect_nodes_from_csv(path: Path) -> set[str]:
    try:
        df = pd.read_csv(path, dtype=str)
    except Exception:
        return set()
    nodes: set[str] = set()
    for col in NODE_COLUMNS & set(df.columns):
        nodes.update(v.strip() for v in df[col].dropna().astype(str) if v.strip())
    return nodes


def collect_nodes_from_db(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with sqlite3.connect(path) as cx:
        row = cx.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'reclamations'"
        ).fetchone()
        if not row:
            return set()
        nodes = set()
        for (value,) in cx.execute("SELECT node_retenu FROM reclamations WHERE node_retenu IS NOT NULL"):
            if value:
                nodes.add(str(value).strip())
        return nodes


def collect_nodes() -> list[str]:
    nodes: set[str] = set()
    for base in (ROOT / "data", ROOT / "resultats"):
        if base.exists():
            for path in base.rglob("*.csv"):
                nodes.update(collect_nodes_from_csv(path))

    nodes.update(collect_nodes_from_db(DB))

    for path in [ROOT / "rapport.tex"]:
        if path.exists():
            text = read_text(path) or ""
            nodes.update(NODE_RE.findall(text))

    return sorted(n for n in nodes if n.startswith("B5G4G_"))


def load_or_create_mapping(nodes: list[str]) -> dict[str, str]:
    existing: dict[str, str] = {}
    if MAPPING.exists():
        with MAPPING.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing[row["real_node"]] = row["anon_node"]

    next_id = len(existing) + 1
    for node in nodes:
        if node not in existing:
            existing[node] = f"NODE_{next_id:04d}"
            next_id += 1

    with MAPPING.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["real_node", "anon_node"])
        writer.writeheader()
        for real, anon in sorted(existing.items(), key=lambda x: x[1]):
            writer.writerow({"real_node": real, "anon_node": anon})
    return existing


def replace_text(text: str, mapping: dict[str, str]) -> str:
    for real in sorted(mapping, key=len, reverse=True):
        text = text.replace(real, mapping[real])
    return text


def anonymize_text_files(mapping: dict[str, str]) -> tuple[int, list[str]]:
    changed = 0
    locked: list[str] = []
    candidates = [ROOT / "rapport.tex"]
    for base in (ROOT / "data", ROOT / "resultats"):
        if base.exists():
            candidates.extend(p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES)

    for path in candidates:
        if path.resolve() == MAPPING.resolve() or not path.exists():
            continue
        text = read_text(path)
        if text is None:
            continue
        new = replace_text(text, mapping)
        if new != text:
            try:
                write_text(path, new)
                changed += 1
            except PermissionError:
                locked.append(str(path.relative_to(ROOT)))
    return changed, locked


def anonymize_db(mapping: dict[str, str]) -> int:
    if not DB.exists():
        return 0
    changed = 0
    with sqlite3.connect(DB) as cx:
        cx.row_factory = sqlite3.Row
        row = cx.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'reclamations'"
        ).fetchone()
        if not row:
            return 0
        columns = [r["name"] for r in cx.execute("PRAGMA table_info(reclamations)")]
        text_columns = [c for c in columns if c != "ticket_id"]
        rows = cx.execute("SELECT * FROM reclamations").fetchall()
        for db_row in rows:
            updates = {}
            for col in text_columns:
                value = db_row[col]
                if isinstance(value, str):
                    new = replace_text(value, mapping)
                    if new != value:
                        updates[col] = new
            if updates:
                assignments = ", ".join(f"{col} = ?" for col in updates)
                cx.execute(
                    f"UPDATE reclamations SET {assignments} WHERE ticket_id = ?",
                    [*updates.values(), db_row["ticket_id"]],
                )
                changed += 1
        cx.commit()
    return changed


def main() -> None:
    nodes = collect_nodes()
    mapping = load_or_create_mapping(nodes)
    text_files, locked = anonymize_text_files(mapping)
    db_rows = anonymize_db(mapping)
    print(f"{len(mapping)} nodes in {MAPPING.name}")
    print(f"{text_files} text files updated")
    print(f"{db_rows} SQLite rows updated")
    if locked:
        print("Locked files not updated:")
        for path in locked:
            print(f"- {path}")


if __name__ == "__main__":
    main()
