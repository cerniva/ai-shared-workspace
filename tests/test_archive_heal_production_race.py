"""Run the *production* archive healer against a corrupt concurrent Git history.

Uses a disposable bare Git remote; never pushes to the real repository.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/archive-heal.yml'


def cmd(*args: str, cwd: Path | None = None) -> str:
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise AssertionError(f'{args}: exit={p.returncode}\nstdout={p.stdout[-800:]}\nstderr={p.stderr[-800:]}')
    return p.stdout.strip()


def commit(repo: Path, message: str) -> None:
    cmd('git', 'add', '.', cwd=repo)
    cmd('git', '-c', 'user.name=test', '-c', 'user.email=test@example.org', 'commit', '-m', message, cwd=repo)


def shell_block() -> str:
    lines = WORKFLOW.read_text(encoding='utf-8').splitlines()
    start = lines.index('      - name: Commit healed archives only')
    run = lines.index('        run: |', start)
    body = []
    for line in lines[run + 1:]:
        if line and not line.startswith('          '):
            break
        body.append(line[10:] if line.startswith('          ') else '')
    return '\n'.join(body) + '\n'


class ArchiveHealProductionRaceTests(unittest.TestCase):
    def test_production_healer_repairs_corrupt_concurrent_commit(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            origin, producer, healer, writer = [base / name for name in ('origin.git', 'producer', 'healer', 'writer')]
            cmd('git', 'init', '--bare', str(origin))
            cmd('git', 'clone', str(origin), str(producer))
            cmd('git', 'checkout', '-b', 'main', cwd=producer)
            for folder in ('scripts', 'messages', 'config', 'knowledge'):
                (producer / folder).mkdir()
            for name in ('archive_heal.py', 'archive_record_guard.py'):
                shutil.copyfile(ROOT / 'scripts' / name, producer / 'scripts' / name)
            (producer / 'scripts/__init__.py').write_text('', encoding='utf-8')
            (producer / 'config/archive_heal_notes.json').write_text('{}\n', encoding='utf-8')
            (producer / 'messages/grok-to-chatgpt.md').write_text(
                '---\nid: MSG-BASE\nfrom: grok\nstatus: seen\n', encoding='utf-8')
            (producer / 'messages/team-reports.md').write_text('## RPT-BASE\n', encoding='utf-8')
            (producer / 'knowledge/lessons.md').write_text('# lessons\n', encoding='utf-8')
            commit(producer, 'good archive')
            cmd('git', 'push', '-u', 'origin', 'main', cwd=producer)
            cmd('git', 'clone', '-b', 'main', str(origin), str(healer))
            cmd('git', 'clone', '-b', 'main', str(origin), str(writer))
            (writer / 'messages/grok-to-chatgpt.md').write_text(
                'SEE_FILE\n\n---\nid: MSG-CONCURRENT\nfrom: grok\nstatus: seen\n',
                encoding='utf-8')
            commit(writer, 'corrupt archive with new record')
            cmd('git', 'push', 'origin', 'main', cwd=writer)
            cmd('bash', '-c', shell_block(), cwd=healer)
            healed = cmd('git', 'show', 'HEAD:messages/grok-to-chatgpt.md', cwd=healer)
            self.assertIn('id: MSG-BASE', healed)
            self.assertIn('id: MSG-CONCURRENT', healed)
            self.assertNotIn('SEE_FILE', healed)
            first_sha = cmd('git', 'rev-parse', 'HEAD', cwd=healer)
            cmd('bash', '-c', shell_block(), cwd=healer)
            self.assertEqual(first_sha, cmd('git', 'rev-parse', 'HEAD', cwd=healer))


if __name__ == '__main__':
    unittest.main()
