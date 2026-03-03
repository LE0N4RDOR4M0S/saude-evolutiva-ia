import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta


class RepositoryPreparationError(Exception):
    pass


@dataclass
class PreparedRepository:
    path: str
    source_id: str
    revision: str


class RepositorySourceManager:
    def __init__(self, base_cache_dir: str = None, git_timeout: int = 180, cache_ttl_hours: int = 24):
        self.base_cache_dir = base_cache_dir or os.path.join(tempfile.gettempdir(), "repo-health-ai-cache")
        self.git_timeout = git_timeout
        self.cache_ttl_hours = cache_ttl_hours
        os.makedirs(self.base_cache_dir, exist_ok=True)

    @staticmethod
    def is_valid_remote_url(repo_url: str) -> bool:
        if not repo_url:
            return False
        pattern = r"^(https://|ssh://|git@).+"
        return bool(re.match(pattern, repo_url.strip()))

    def cleanup_stale_cache(self) -> None:
        cutoff = datetime.now() - timedelta(hours=self.cache_ttl_hours)
        for entry in os.scandir(self.base_cache_dir):
            if not entry.is_dir():
                continue
            modified_at = datetime.fromtimestamp(entry.stat().st_mtime)
            if modified_at < cutoff:
                shutil.rmtree(entry.path, ignore_errors=True)

    def prepare_local_repository(self, repo_path: str) -> PreparedRepository:
        #Local if not repo_path:
        #Local     raise RepositoryPreparationError("Caminho local não informado.")
        #Local if not os.path.exists(repo_path):
        #Local     raise RepositoryPreparationError(f"Caminho inválido: {repo_path}")
        #Local if not os.path.isdir(os.path.join(repo_path, ".git")):
        #Local     raise RepositoryPreparationError("O caminho informado não é um repositório Git válido.")
        #Local revision = self._run_git_command(["-C", repo_path, "rev-parse", "HEAD"]).strip()
        #Local return PreparedRepository(path=repo_path, source_id=f"local:{repo_path}", revision=revision)
        raise RepositoryPreparationError("Processamento de repositório local desativado. Use URL remota.")

    def prepare_remote_repository(self, repo_url: str, depth: int) -> PreparedRepository:
        if not self.is_valid_remote_url(repo_url):
            raise RepositoryPreparationError("URL de repositório inválida. Use https://, ssh:// ou git@.")

        normalized_url = repo_url.strip()
        normalized_depth = max(10, int(depth))
        repository_hash = hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()[:16]
        target_dir = os.path.join(self.base_cache_dir, repository_hash)

        if not os.path.exists(target_dir):
            self._run_git_command([
                "clone",
                "--filter=blob:none",
                f"--depth={normalized_depth}",
                normalized_url,
                target_dir,
            ])
        else:
            if not os.path.isdir(os.path.join(target_dir, ".git")):
                shutil.rmtree(target_dir, ignore_errors=True)
                self._run_git_command([
                    "clone",
                    "--filter=blob:none",
                    f"--depth={normalized_depth}",
                    normalized_url,
                    target_dir,
                ])
            else:
                existing_origin = self._run_git_command([
                    "-C", target_dir, "remote", "get-url", "origin"
                ]).strip()
                if existing_origin != normalized_url:
                    shutil.rmtree(target_dir, ignore_errors=True)
                    self._run_git_command([
                        "clone",
                        "--filter=blob:none",
                        f"--depth={normalized_depth}",
                        normalized_url,
                        target_dir,
                    ])
                else:
                    self._run_git_command([
                        "-C", target_dir, "fetch", "origin", f"--depth={normalized_depth}", "--prune"
                    ])
                    self._run_git_command(["-C", target_dir, "reset", "--hard", "FETCH_HEAD"])

        revision = self._run_git_command(["-C", target_dir, "rev-parse", "HEAD"]).strip()
        return PreparedRepository(path=target_dir, source_id=f"remote:{normalized_url}", revision=revision)

    def _run_git_command(self, args):
        command = ["git", *args]
        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.git_timeout,
                check=True,
            )
            return process.stdout
        except FileNotFoundError as exc:
            raise RepositoryPreparationError("Git não encontrado no ambiente de execução.") from exc
        except subprocess.TimeoutExpired as exc:
            raise RepositoryPreparationError("Timeout ao executar comando Git.") from exc
        except subprocess.CalledProcessError as exc:
            error_output = (exc.stderr or "").strip() or (exc.stdout or "").strip()
            raise RepositoryPreparationError(f"Falha no comando Git: {error_output}") from exc
