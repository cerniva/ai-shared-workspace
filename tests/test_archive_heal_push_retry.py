"""A concurrent append after fetch must force a push retry without losing records.

This test runs the real workflow shell in disposable Git repositories, with a
minimal deterministic healer stub. It never pushes to the production remote.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.test_archive_heal_workflow_race import run, workflow_shell


class ArchiveHealPushRetryTests(unittest.TestCase):
    def test_push_rejected_by_concurrent_append_then_repaired(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            origin, producer, healer, writer = (
                root / name for name in ('origin.git', 'producer', 'healer', 'writer')
            )
            run('git', 'init', '--bare', str(origin))
            run('git', 'clone', str(origin), str(producer))
            run('git', 'checkout', '-b', 'main', cwd=producer)
            for folder in ('messages', 'scripts', 'config', 'knowledge'):
                (producer / folder).mkdir()
            (producer / 'messages/grok-to-chatgpt.md').write_text(
                '---\nid: base\nstatus: seen\n', encoding='utf-8'
            )
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
            run('git', '-c', 'user.name=test', '-c', 'user.email=test@example.org',
                'commit', '-m', 'base', cwd=producer)
            run('git', 'push', '-u', 'origin', 'main', cwd=producer)
            run('git', 'clone', '-b', 'main', str(origin), str(healer))
            run('git', 'clone', '-b', 'main', str(origin), str(writer))

            # Git runs this hook *after* receiving remote refs but *before*
            # sending the healer's first push. Another writer advances main.
            marker = healer / '.git' / 'race-hook-fired'
            hook = healer / '.git' / 'hooks' / 'pre-push'
            hook.write_text(
                '#!/bin/sh\n'
                f'if [ ! -e "{marker}" ]; then\n'
                f'  touch "{marker}"\n'
                f'  printf "%s\\n" "---" "id: racing" "status: seen" >> "{writer / "messages/grok-to-chatgpt.md"}"\n'
                f'  git -C "{writer}" add -- messages/grok-to-chatgpt.md\n'
                f'  git -C "{writer}" -c user.name=test -c user.email=test@example.org commit -m racing >/dev/null\n'
                f'  git -C "{writer}" push origin HEAD:main >/dev/null 2>&1 || exit 1\n'
                'fi\n',
                encoding='utf-8',
            )
            hook.chmod(0o755)
            run('bash', '-c', workflow_shell(), cwd=healer)
            self.assertTrue(marker.exists(), 'the concurrent writer hook did not run')
            result = run('git', 'show', 'HEAD:messages/grok-to-chatgpt.md', cwd=healer)
            self.assertEqual(result.count('id: base'), 1)
            self.assertEqual(result.count('id: racing'), 1)
            self.assertEqual(result.count('id: note-repaired'), 1)
            self.assertEqual(run('git', '--git-dir', str(origin), 'rev-parse', 'main'),
                             run('git', 'rev-parse', 'HEAD', cwd=healer))
            first_sha = run('git', 'rev-parse', 'HEAD', cwd=healer)
            run('bash', '-c', workflow_shell(), cwd=healer)
            self.assertEqual(first_sha, run('git', 'rev-parse', 'HEAD', cwd=healer))


if __name__ == '__main__':
    unittest.main()
