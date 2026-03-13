import subprocess
from functools import cached_property
from pathlib import Path

from pydantic import BaseModel, FilePath, Field

from ai_review.libs.resources import load_resource


def resolve_prompt_files(files: list[FilePath] | None, default_file: str) -> list[Path]:
    return files or [
        load_resource(
            package="ai_review.prompts",
            filename=default_file,
            fallback=f"ai_review/prompts/{default_file}"
        )
    ]


def resolve_system_prompt_files(files: list[FilePath] | None, include: bool, default_file: str) -> list[Path]:
    global_files = [
        load_resource(
            package="ai_review.prompts",
            filename=default_file,
            fallback=f"ai_review/prompts/{default_file}"
        )
    ]

    if files is None:
        return global_files

    if include:
        return global_files + files

    return files


class PromptConfig(BaseModel):
    context: dict[str, str] = Field(default_factory=dict)
    normalize_prompts: bool = True
    context_placeholder: str = "<<{value}>>"
    include_agents_md: bool = True

    # --- Prompts ---
    inline_prompt_files: list[FilePath] | None = None
    context_prompt_files: list[FilePath] | None = None
    summary_prompt_files: list[FilePath] | None = None
    inline_reply_prompt_files: list[FilePath] | None = None
    summary_reply_prompt_files: list[FilePath] | None = None

    # --- System Prompts ---
    system_inline_prompt_files: list[FilePath] | None = None
    system_context_prompt_files: list[FilePath] | None = None
    system_summary_prompt_files: list[FilePath] | None = None
    system_inline_reply_prompt_files: list[FilePath] | None = None
    system_summary_reply_prompt_files: list[FilePath] | None = None

    # --- Include System Prompts ---
    include_inline_system_prompts: bool = True
    include_context_system_prompts: bool = True
    include_summary_system_prompts: bool = True
    include_inline_reply_system_prompts: bool = True
    include_summary_reply_system_prompts: bool = True

    # --- Load AGENTS.md ---
    def _get_git_repo_root(self) -> Path | None:
        """Get the root directory of the current git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            repo_root = result.stdout.strip()
            if repo_root:
                return Path(repo_root)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return None

    def _load_agents_md(self) -> str | None:
        """Load AGENTS.md from the git repository root if it exists."""
        if not self.include_agents_md:
            return None

        # Try to get the git repository root
        repo_root = self._get_git_repo_root()
        if repo_root:
            agents_md_path = repo_root / "AGENTS.md"
            if agents_md_path.exists():
                print(f"Loading AGENTS.md from: {agents_md_path}")
                return agents_md_path.read_text(encoding="utf-8")

        return None

    # --- Prompts ---
    @cached_property
    def inline_prompt_files_or_default(self) -> list[Path]:
        return resolve_prompt_files(self.inline_prompt_files, "default_inline.md")

    @cached_property
    def context_prompt_files_or_default(self) -> list[Path]:
        return resolve_prompt_files(self.context_prompt_files, "default_context.md")

    @cached_property
    def summary_prompt_files_or_default(self) -> list[Path]:
        return resolve_prompt_files(self.summary_prompt_files, "default_summary.md")

    @cached_property
    def inline_reply_prompt_files_or_default(self) -> list[Path]:
        return resolve_prompt_files(self.inline_reply_prompt_files, "default_inline_reply.md")

    @cached_property
    def summary_reply_prompt_files_or_default(self) -> list[Path]:
        return resolve_prompt_files(self.summary_reply_prompt_files, "default_summary_reply.md")

    # --- System Prompts ---
    @cached_property
    def system_inline_prompt_files_or_default(self) -> list[Path]:
        return resolve_system_prompt_files(
            files=self.system_inline_prompt_files,
            include=self.include_inline_system_prompts,
            default_file="default_system_inline.md"
        )

    @cached_property
    def system_context_prompt_files_or_default(self) -> list[Path]:
        return resolve_system_prompt_files(
            files=self.system_context_prompt_files,
            include=self.include_context_system_prompts,
            default_file="default_system_context.md"
        )

    @cached_property
    def system_summary_prompt_files_or_default(self) -> list[Path]:
        return resolve_system_prompt_files(
            files=self.system_summary_prompt_files,
            include=self.include_summary_system_prompts,
            default_file="default_system_summary.md"
        )

    @cached_property
    def system_inline_reply_prompt_files_or_default(self) -> list[Path]:
        return resolve_system_prompt_files(
            files=self.system_inline_reply_prompt_files,
            include=self.include_inline_reply_system_prompts,
            default_file="default_system_inline_reply.md"
        )

    @cached_property
    def system_summary_reply_prompt_files_or_default(self) -> list[Path]:
        return resolve_system_prompt_files(
            files=self.system_summary_reply_prompt_files,
            include=self.include_summary_reply_system_prompts,
            default_file="default_system_summary_reply.md"
        )

    # --- Load Prompts ---
    def load_inline(self) -> list[str]:
        return [file.read_text(encoding="utf-8") for file in self.inline_prompt_files_or_default]

    def load_context(self) -> list[str]:
        return [file.read_text(encoding="utf-8") for file in self.context_prompt_files_or_default]

    def load_summary(self) -> list[str]:
        return [file.read_text(encoding="utf-8") for file in self.summary_prompt_files_or_default]

    def load_inline_reply(self) -> list[str]:
        return [file.read_text(encoding="utf-8") for file in self.inline_reply_prompt_files_or_default]

    def load_summary_reply(self) -> list[str]:
        return [file.read_text(encoding="utf-8") for file in self.summary_reply_prompt_files_or_default]

    # --- Load System Prompts ---
    def _load_with_agents_md(self, files: list[Path]) -> list[str]:
        """Load prompt files and prepend AGENTS.md if available."""
        prompts = [file.read_text(encoding="utf-8") for file in files]
        agents_md = self._load_agents_md()
        if agents_md:
            prompts.insert(0, agents_md)
        return prompts

    def load_system_inline(self) -> list[str]:
        return self._load_with_agents_md(self.system_inline_prompt_files_or_default)

    def load_system_context(self) -> list[str]:
        return self._load_with_agents_md(self.system_context_prompt_files_or_default)

    def load_system_summary(self) -> list[str]:
        return self._load_with_agents_md(self.system_summary_prompt_files_or_default)

    def load_system_inline_reply(self) -> list[str]:
        return self._load_with_agents_md(self.system_inline_reply_prompt_files_or_default)

    def load_system_summary_reply(self) -> list[str]:
        return self._load_with_agents_md(self.system_summary_reply_prompt_files_or_default)
