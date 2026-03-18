"""storage/vault_writer.py"""
import re
from datetime import date
from pathlib import Path

from processing.result_handler import ProcessedResult


class VaultWriter:
    def __init__(self, vault: Path):
        self._vault = vault
        self._folders = {
            "moc":       vault / "00-MOC",
            "permanent": vault / "30-Permanent",
        }
        for f in self._folders.values():
            f.mkdir(parents=True, exist_ok=True)

    def write(self, result: ProcessedResult, content: str) -> Path:
        path = self._note_path(result)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self._update_moc(result.topic, result.domain)
        return path

    # ── private ──────────────────────────────────────────────────────────────

    def _note_path(self, result: ProcessedResult) -> Path:
        safe = re.sub(r'[\\/*?:"<>|]', "", result.topic)
        return self._folders["permanent"] / result.domain / f"{safe}.md"

    def _update_moc(self, topic: str, domain: str) -> None:
        moc = self._folders["moc"] / f"{domain} MOC.md"
        entry = f"- [[{topic}]] — {date.today()}\n"
        if moc.exists():
            text = moc.read_text(encoding="utf-8")
            if f"[[{topic}]]" not in text:
                moc.write_text(text + entry, encoding="utf-8")
        else:
            moc.write_text(f"# {domain} MOC\n\n{entry}", encoding="utf-8")
