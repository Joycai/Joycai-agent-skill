"""Run: python3 -m unittest discover -s <this directory> -v"""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('dashboard', Path(__file__).resolve().parents[1] / 'dashboard.py')
dashboard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dashboard)
# Valid 1x1 PNG, no image dependencies.
PNG = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.quiet = contextlib.redirect_stdout(io.StringIO())
        self.quiet.__enter__()
        self.no_sips = patch.object(dashboard.shutil, 'which', return_value=None)
        self.no_sips.start()
        dashboard.init(self.root)

    def tearDown(self):
        self.no_sips.stop()
        self.quiet.__exit__(None, None, None)
        self.temp.cleanup()

    def task(self):
        d = self.root / 'tasks/t1'
        d.mkdir(exist_ok=True)
        (d / 'output #1.png').write_bytes(PNG)
        (d / 'prompt.txt').write_text('</script><script>alert("x")</script>\n真实 prompt', encoding='utf-8')
        task = {'id': 't1', 'title': '任务一', 'kind': 'generate', 'status': 'completed', 'steps': [
            {'id': 's1', 'version': 'V1', 'status': 'failed', 'model': 'A', 'inputs': [], 'outputs': [], 'error': 'tool failed'},
            {'id': 's2', 'version': 'V2', 'status': 'completed', 'model': 'B', 'parameters': {'size': '2K'},
             'prompt': {'path': 'tasks/t1/prompt.txt'},
             'inputs': [{'path': 'references/missing.png', 'role': '服装参考', 'sent': None}],
             'outputs': [{'id': 'o1', 'path': 'tasks/t1/output #1.png'}]}]}
        dashboard.dump(d / 'task.json', task)
        return task

    def test_initialization_preserves_existing_registry_and_sources(self):
        path = self.root / '.studio/project.json'
        p = dashboard.load(path)
        p['title'] = '保留标题'
        dashboard.dump(path, p)
        before = path.read_bytes()
        (self.root / 'references/untouched.png').write_bytes(PNG)
        dashboard.init(self.root, '不能覆盖')
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual((self.root / 'references/untouched.png').read_bytes(), PNG)
        self.assertTrue((self.root / 'dashboard/index.html').exists())

    def test_workspace_initializer_keeps_custom_rules_and_index(self):
        import runpy
        initializer = Path(__file__).resolve().parents[3] / 'reference-image-workspace/scripts/init_workspace.py'
        (self.root / 'AGENTS.md').write_text('Custom project rules', encoding='utf-8')
        (self.root / 'references/INDEX.md').write_text('Existing index', encoding='utf-8')
        initialize = runpy.run_path(str(initializer))['initialize']
        initialize(self.root)
        initialize(self.root)
        self.assertEqual((self.root / 'AGENTS.md').read_text(), 'Custom project rules')
        self.assertEqual((self.root / 'references/INDEX.md').read_text(), 'Existing index')
        self.assertTrue((self.root / 'REFERENCE_WORKSPACE.md').exists())
        self.assertTrue((self.root / 'dashboard/index.html').exists())

    def test_attempt_provenance_missing_files_and_prompt_escaping(self):
        self.task()
        data = dashboard.build(self.root)
        steps = data['tasks'][0]['steps']
        self.assertEqual(steps[0]['status'], 'failed')
        self.assertEqual(steps[0]['outputs'], [])
        self.assertEqual(steps[1]['model'], 'B')
        self.assertIsNone(steps[1]['inputs'][0]['sent'])
        self.assertEqual(steps[1]['outputs'][0]['asset']['dimensions'], [1, 1])
        self.assertIn('%23', steps[1]['outputs'][0]['asset']['url'])
        self.assertEqual(data['warnings'], ['Missing file: references/missing.png'])
        html = (self.root / 'dashboard/index.html').read_text()
        self.assertNotIn('</script><script>alert', html)
        self.assertIn('\\u003c/script', html)
        self.assertEqual((self.root / 'tasks/t1/output #1.png').read_bytes(), PNG)

    def test_deleted_output_keeps_history_without_missing_warning(self):
        self.task()
        name = 'tasks/t1/output #1.png'
        (self.root / name).unlink()
        project, _ = dashboard.read_project(self.root)
        project['archives'] = [{'path': name, 'archived': True, 'deleted': True,
            'deleted_at': '2026-10-15T07:00:00+00:00', 'reason': 'User requested permanent deletion',
            'history': [{'action': 'permanent-delete'}]}]
        dashboard.dump(self.root / '.studio/project.json', project)
        data = dashboard.build(self.root)
        asset = data['tasks'][0]['steps'][1]['outputs'][0]['asset']
        self.assertTrue(asset['deleted'])
        self.assertFalse(asset['exists'])
        self.assertEqual(asset['deletion_reason'], 'User requested permanent deletion')
        self.assertEqual(data['warnings'], ['Missing file: references/missing.png'])
        self.assertEqual(data['tasks'][0]['steps'][1]['outputs'][0]['id'], 'o1')
        self.assertIn('真实 prompt', data['tasks'][0]['steps'][1]['prompt']['text'])
        # A reappearing file is not silently treated as a successful deletion.
        (self.root / name).write_bytes(PNG)
        self.assertIn('Marked deleted but file exists: ' + name, dashboard.build(self.root)['warnings'])

    def test_unsupported_deletion_marker_does_not_hide_missing_file(self):
        self.task()
        name = 'tasks/t1/output #1.png'
        (self.root / name).unlink()
        task = dashboard.load(self.root / 'tasks/t1/task.json')
        task['steps'][1]['outputs'][0]['deleted'] = True
        dashboard.dump(self.root / 'tasks/t1/task.json', task)
        self.assertIn('Missing file: ' + name, dashboard.build(self.root)['warnings'])
        project, _ = dashboard.read_project(self.root)
        project['archives'] = [{'path': name, 'archived': True, 'deleted': True,
                               'deleted_at': 'today', 'reason': 'x', 'history': []}]
        dashboard.dump(self.root / '.studio/project.json', project)
        with self.assertRaisesRegex(ValueError, 'permanent-delete history'):
            dashboard.build(self.root)

    def test_new_images_are_not_silently_confirmed(self):
        (self.root / 'references/new.png').write_bytes(PNG)
        data = dashboard.build(self.root)
        self.assertEqual(data['references'], [])
        self.assertEqual(len(data['unregistered']), 1)

    def test_registration_is_idempotent_and_retains_lineage(self):
        self.task()
        (self.root / 'retained/keep.png').write_bytes(PNG)
        record = {'id': 'K1', 'title': '保留', 'path': 'retained/keep.png', 'scope': '作品',
                  'status': 'retained', 'confirmation': '用户说保留', 'origin': {'task': 't1', 'step': 's2', 'output': 'o1'}}
        dashboard.dump(self.root / '.studio/keep.json', record)
        for _ in range(2): dashboard.record(self.root, 'retained', '.studio/keep.json')
        project, _ = dashboard.read_project(self.root)
        self.assertEqual(len(project['retained']), 1)
        self.assertEqual(project['references'], [])
        (self.root / 'retained/keep.png').write_bytes(PNG + b'changed')
        with self.assertRaisesRegex(ValueError, 'differs'): dashboard.build(self.root)

    def test_bad_origin_and_duplicate_ids_fail(self):
        task = self.task()
        project, _ = dashboard.read_project(self.root)
        project['retained'] = [{'id':'K1','title':'x','path':'retained/x.png','scope':'作品','status':'retained',
                                'confirmation':'保留','origin':{'task':'t1','step':'s1','output':'missing'}}]
        with self.assertRaisesRegex(ValueError, 'Unknown origin'): dashboard.validate(project, [task])
        project['retained'] = []
        task['steps'].append(task['steps'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate id'): dashboard.validate(project, [task])

    def test_paths_and_symlink_escape_rejected(self):
        for path in ['/etc/passwd', '../outside.png', 'https://example.com/image.png']:
            with self.assertRaises(ValueError): dashboard.local(self.root, path)
        (self.root / 'references/link').symlink_to(self.root.parent)
        with self.assertRaises(ValueError): dashboard.local(self.root, 'references/link/secret')

    def test_invalid_reference_does_not_replace_registry(self):
        path = self.root / '.studio/project.json'
        before = path.read_bytes()
        record = {'id':'R1','title':'x','path':'references/new.png','status':'confirmed','scope':'全身','source':'user'}
        dashboard.dump(self.root / '.studio/ref.json', record)
        with self.assertRaises(ValueError): dashboard.record(self.root, 'reference', '.studio/ref.json')
        self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__': unittest.main()
