"""Regression guard for archive-heal workflow's fresh-main retry contract.

The Git race uses a controlled healer stub. It does not prove that the real
archive_heal.py can repair every production history; those checks stay separate.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/archive-heal.yml'


def workflow_shell() -> str:
    lines = WORKFLOW.read_text(encoding='utf-8').splitlines()
    start = lines.index('      - name: Commit healed archives only')
    run_line = lines.index('        run: |', start)
    body = []
    for line in lines[run_line + 1:]:
        if line and not line.startswith('          '):
            break
        body.append(line[10:] if line.startswith('          ') else '')
    if not body:
        raise AssertionError('workflow shell block missing')
    return '\n'.join(body) + '\n'


def run(*args: str, cwd: Path | None = None) -> str:
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=30)
    if p.returncode:
        raise AssertionError(f'command {args} exit={p.returncode}: {p.stderr[-1500:]}')
    return p.stdout.strip()


class ArchiveHealFreshMainTests(unittest.TestCase):
    def test_shell_syntax_and_safety_contract(self) -> None:
        shell = workflow_shell()
        run('bash', '-n', '-c', shell)
        self.assertIn('git fetch origin main', shell)
        self.assertIn('git reset --hard origin/main', shell)
        self.assertIn('python3 scripts/archive_heal.py --check', shell)
        self.assertIn('python3 -m json.tool config/archive_heal_notes.json', shell)
        self.assertNotIn('git pull --rebase', shell)
        self.assertNotIn('git push --force', shell)
        self.assertIn('git fetch origin main && [[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]', shell)
        self.assertIn('archive-heal: remote read-back mismatch', shell)
        self.assertIn('git add -- messages/grok-to-chatgpt.md messages/team-reports.md knowledge/lessons.md', shell)

    def test_non_main_dispatch_fails_before_archive_write(self) -> None:
        workflow = WORKFLOW.read_text(encoding='utf-8')
        guard_name = '      - name: Reject non-main workflow dispatch before archive writes'
        heal_name = '      - name: Heal archives from git history (fail-closed)'
        self.assertLess(workflow.index(guard_name), workflow.index(heal_name))
        lines = workflow.splitlines()
        start = lines.index(guard_name)
        run_line = lines.index('        run: |', start)
        body = []
        for line in lines[run_line + 1:]:
            if line and not line.startswith('          '):
                break
            body.append(line[10:] if line.startswith('          ') else '')
        shell = '\n'.join(body) + '\n'
        run('bash', '-n', '-c', shell)
        for ref, expected_exit in (
            ('refs/heads/main', 0),
            ('refs/heads/feature', 1),
            ('refs/tags/v1', 1),
            ('', 1),
        ):
            with self.subTest(ref=ref):
                env = dict(os.environ, GITHUB_REF=ref)
                proc = subprocess.run(['bash', '-c', shell], env=env,
                                      capture_output=True, text=True, timeout=10)
                self.assertEqual(proc.returncode, expected_exit, proc.stderr)
                if expected_exit:
                    self.assertIn('refusing non-main ref', proc.stderr)

    def test_stale_checkout_preserves_concurrent_archive_record(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            origin, producer, healer, writer = (root / name for name in ('origin.git', 'producer', 'healer', 'writer'))
            run('git', 'init', '--bare', str(origin))
            run('git', 'clone', str(origin), str(producer))
            run('git', 'checkout', '-b', 'main', cwd=producer)
            for folder in ('messages', 'scripts', 'config', 'knowledge'):
                (producer / folder).mkdir()
            (producer / 'messages/grok-to-chatgpt.md').write_text('---\nid: base\nstatus: seen\n', encoding='utf-8')
            (producer / 'messages/team-reports.md').write_text('## RPT-BASE\n', encoding='utf-8')
            (producer / 'knowledge/lessons.md').write_text('# lessons\n', encoding='utf-8')
            (producer / 'config/archive_heal_notes.json').write_text('{}\n', encoding='utf-8')
            (producer / 'scripts/archive_heal.py').write_text(
                'from pathlib import Path\nimport sys\n'
                'p=Path("messages/grok-to-chatgpt.md")\n'
                's=p.read_text()\n'
                'if "--check" in sys.argv:\n'
                '    sys.exit(1 if "PLACEHOLDER" in s else 0)\n'
                'if "id: note-repaired" not in s:\n'
                '    p.write_text(s+"---\\nid: note-repaired\\nstatus: seen\\n")\n',
                encoding='utf-8',
            )
            run('git', 'add', '.', cwd=producer)
            run('git', '-c', 'user.name=test', '-c', 'user.email=test@example.org', 'commit', '-m', 'base', cwd=producer)
            run('git', 'push', '-u', 'origin', 'main', cwd=producer)
            run('git', 'clone', '-b', 'main', str(origin), str(healer))
            run('git', 'clone', '-b', 'main', str(origin), str(writer))
            with (healer / 'messages/grok-to-chatgpt.md').open('a', encoding='utf-8') as f:
                f.write('---\nid: stale-uncommitted\nstatus: seen\n')
            with (writer / 'messages/grok-to-chatgpt.md').open('a', encoding='utf-8') as f:
                f.write('---\nid: concurrent\nstatus: seen\n')
            run('git', 'add', '.', cwd=writer)
            run('git', '-c', 'user.name=test', '-c', 'user.email=test@example.org', 'commit', '-m', 'concurrent', cwd=writer)
            run('git', 'push', 'origin', 'main', cwd=writer)
            run('bash', '-c', workflow_shell(), cwd=healer)
            result = run('git', 'show', 'main:messages/grok-to-chatgpt.md', cwd=healer)
            self.assertIn('id: concurrent', result)
            self.assertIn('id: note-repaired', result)
            self.assertNotIn('id: stale-uncommitted', result)
            sha_before = run('git', 'rev-parse', 'HEAD', cwd=healer)
            run('bash', '-c', workflow_shell(), cwd=healer)
            self.assertEqual(sha_before, run('git', 'rev-parse', 'HEAD', cwd=healer))


if __name__ == '__main__':
    unittest.main()
