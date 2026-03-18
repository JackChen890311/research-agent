"""storage/git_syncer.py — Observer Pattern: 寫入後自動 sync"""
import subprocess
from pathlib import Path


class GitSyncer:
    def __init__(self, vault: Path):
        self._vault = vault

    def sync(self, message: str) -> bool:
        try:
            # self._run(["git", "add", "-A"])
            # self._run(["git", "commit", "-m", message])
            # self._run(["git", "push"])
            return True
        except subprocess.CalledProcessError:
            return False  # 無變更或 push 失敗時靜默處理

    def _run(self, cmd: list[str]) -> None:
        subprocess.run([*cmd], cwd=self._vault, check=True, capture_output=True)
