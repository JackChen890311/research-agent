"""storage/vault_writer.py"""
import re
from datetime import date
from pathlib import Path

from processing.result_handler import ProcessedResult


class VaultWriter:
    def __init__(self, vault: Path):
        self._vault = vault
        self._folders = {
            "moc":        vault / "00-MOC",
            "fleeting":   vault / "10-Fleeting",
            "literature": vault / "20-Literature",
            "permanent":  vault / "30-Permanent",
        }
        for f in self._folders.values():
            f.mkdir(parents=True, exist_ok=True)

    def write(self, result: ProcessedResult, content: str) -> Path:
        """Write a permanent note and update the domain MOC."""
        path = self._permanent_path(result)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        # Use the actual stem (may include a number suffix) as the MOC link title
        self._update_moc(path.stem, result.domain, result.subcategory)
        return path

    def write_literature(self, domain: str, title: str, content: str) -> Path:
        """Write a literature note (intermediate research artifact). Not added to MOC."""
        safe = _safe_name(title)
        path = self._folders["literature"] / domain / f"{safe}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_fleeting(self, domain: str, title: str, content: str) -> Path:
        """Write a fleeting note (raw user input). Not added to MOC."""
        safe = _safe_name(title)
        path = self._folders["fleeting"] / domain / f"{safe}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    # ── private ──────────────────────────────────────────────────────────────

    def _permanent_path(self, result: ProcessedResult) -> Path:
        safe = _safe_name(result.topic)
        base = self._folders["permanent"] / result.domain
        path = base / f"{safe}.md"
        if not path.exists():
            return path
        n = 2
        while True:
            candidate = base / f"{safe} {n}.md"
            if not candidate.exists():
                return candidate
            n += 1

    def _update_moc(self, topic: str, domain: str, subcategory: str) -> None:
        """
        Update the domain MOC with a sub-category heading.
        Structure:
            # {domain} MOC

            ## {subcategory}
            - [[topic]] — YYYY-MM-DD
        """
        moc = self._folders["moc"] / f"{domain} MOC.md"
        moc.parent.mkdir(parents=True, exist_ok=True)
        entry = f"- [[{topic}]] — {date.today()}\n"

        if moc.exists():
            text = moc.read_text(encoding="utf-8")
            if f"[[{topic}]]" in text:
                return  # already present

            # Try to find the existing sub-category section
            pattern = re.compile(
                rf"(## {re.escape(subcategory)}\n)(.*?)(?=\n## |\Z)",
                re.DOTALL,
            )
            match = pattern.search(text)
            if match:
                # Append entry at the end of the matching section
                new_section = match.group(1) + match.group(2).rstrip() + "\n" + entry
                text = text[: match.start()] + new_section + text[match.end() :]
            else:
                # Create a new sub-category section at the end
                text = text.rstrip() + f"\n\n## {subcategory}\n{entry}"
            moc.write_text(text, encoding="utf-8")
        else:
            moc.write_text(
                f"# {domain} MOC\n\n## {subcategory}\n{entry}",
                encoding="utf-8",
            )


def _safe_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name)
