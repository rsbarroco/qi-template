"""The suite must pass on the QA engineer's machine, not only on the Linux runner.

The baseline for every eval is recorded on Windows. Two whole classes of bug are invisible
on Linux and fatal there: a path spelled with the native separator, and a file opened on
whatever encoding the locale happens to be. Both of these tests read the repository itself,
so they fail on any platform the moment a new call slips through.
"""
from __future__ import annotations

import re
from pathlib import Path

from evals.graders import snapshot

REPO = Path(__file__).resolve().parent.parent
SOURCE_DIRS = ("qi", "evals", "tests")

# A bare builtin open() in text mode decodes on the locale exactly like read_text() does,
# so it counts too. No whitespace before the "(": PEP 8 forbids it in a call, which is what
# keeps the prose in docstrings ("anything you cannot open (no reader...)") out of the net.
IO_CALL = re.compile(r"(?:(?<=\.)(?:read_text|write_text|open)|(?<![\w.])open)\(")
BINARY_MODE = re.compile(r"""^\s*[^,]+,\s*["'][rwax+]*b[rwax+]*["']""")


def source_files() -> list[Path]:
    """Every Python file we ship, including the .py.j2 templates of generated scripts."""
    out = []
    for d in SOURCE_DIRS:
        for p in sorted((REPO / d).rglob("*")):
            name = p.name
            if not (name.endswith(".py") or name.endswith(".py.j2")):
                continue
            if "__pycache__" in p.parts or ".runs" in p.parts:
                continue
            out.append(p)
    return out


def _call_args(text: str, open_paren: int) -> str | None:
    """The argument text of the call whose '(' is at `open_paren`, or None if unbalanced."""
    depth, i, quote = 0, open_paren, None
    while i < len(text):
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if text.startswith(quote, i):
                i += len(quote)
                quote = None
                continue
        elif text.startswith(('"""', "'''"), i):
            quote = text[i:i + 3]
            i += 3
            continue
        elif c in "\"'":
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[open_paren + 1:i]
        i += 1
    return None


def bare_io_calls(path: Path) -> list[str]:
    """Lines in `path` that read or write text without saying which encoding."""
    text = path.read_text(encoding="utf-8")
    offenders = []
    for m in IO_CALL.finditer(text):
        args = _call_args(text, m.end() - 1)
        if args is None or "encoding=" in args:
            continue
        if BINARY_MODE.match(args):      # binary mode takes no encoding
            continue
        if not args.strip():             # a bare open() is prose, not a call
            continue
        line_no = text.count("\n", 0, m.start()) + 1
        offenders.append(f"{path.relative_to(REPO).as_posix()}:{line_no}")
    return offenders


def test_text_io_always_names_its_encoding():
    """No read or write anywhere in the repo may fall back to the locale.

    cp1252 cannot decode the em dash our own templates are full of, nor encode the ✅ and
    ❌ the spec tables use. Every such call is a crash on the QA engineer's machine and a
    pass on the Linux runner.
    """
    offenders = [line for path in source_files() for line in bare_io_calls(path)]
    assert not offenders, "text I/O without encoding=:\n  " + "\n  ".join(offenders)


def test_snapshot_keys_are_posix_on_every_platform(tmp_path):
    """Graders match changed files against prefixes the case files spell with "/".

    A Windows-native key makes `dir_unchanged` and `only_changed_under` report "no
    changes" over a directory the agent rewrote — a false pass, the worst kind.
    """
    (tmp_path / "tests" / "cart").mkdir(parents=True)
    (tmp_path / "tests" / "cart" / "add-item.spec.ts").write_text("x", encoding="utf-8")

    keys = list(snapshot(tmp_path))

    assert keys == ["tests/cart/add-item.spec.ts"]
    assert all("\\" not in k for k in keys)
