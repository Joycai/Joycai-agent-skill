import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dashboard
import lifecycle

PNG=bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.quiet=contextlib.redirect_stdout(io.StringIO());self.quiet.__enter__()
        self.no_sips=patch.object(dashboard.shutil,'which',return_value=None);self.no_sips.start()
        dashboard.init(self.root)
        self.path='tasks/t1/v1.png';folder=self.root/'tasks/t1';folder.mkdir();(self.root/self.path).write_bytes(PNG)
        self.task={'id':'t1','title':'Test','kind':'generate','status':'completed','steps':[
            {'id':'v1','version':'V1','status':'completed','prompt':{'text':'original prompt'},'outputs':[{'id':'O1','path':self.path}]},
            {'id':'v2','version':'V2','status':'completed','inputs':[{'path':self.path,'role':'previous result','sent':True}],'outputs':[]}]}
        dashboard.dump(folder/'task.json',self.task)
    def tearDown(self):
        self.no_sips.stop();self.quiet.__exit__(None,None,None);self.temp.cleanup()
    def test_archive_and_restore_preserve_referenced_inputs_and_bytes(self):
        before=(self.root/'tasks/t1/task.json').read_bytes()
        report=lifecycle.update(self.root,[self.path],'user requests cleanup')
        self.assertTrue(any('/inputs/' in ref for ref in report[0]['references']))
        data=dashboard.build(self.root)
        self.assertTrue(data['tasks'][0]['steps'][1]['inputs'][0]['asset']['exists'])
        self.assertTrue(data['tasks'][0]['steps'][0]['outputs'][0]['asset']['archived'])
        self.assertEqual(len(data['archives']),1)
        self.assertEqual((self.root/self.path).read_bytes(),PNG)
        self.assertEqual((self.root/'tasks/t1/task.json').read_bytes(),before)
        lifecycle.update(self.root,[self.path],'restore',restore=True)
        self.assertEqual(dashboard.build(self.root)['archives'],[])
        project,_=dashboard.read_project(self.root)
        self.assertEqual([x['action'] for x in project['archives'][0]['history']],['archive','restore'])
    def test_protected_and_missing_targets_do_not_change_registry(self):
        project,_=dashboard.read_project(self.root)
        project['references']=[{'id':'R1','title':'approved','path':self.path,'scope':'costume','status':'confirmed','confirmation':'user approved','source':'user'}]
        path=self.root/'.studio/project.json';dashboard.dump(path,project);before=path.read_bytes()
        with self.assertRaisesRegex(ValueError,'reference or retained'):lifecycle.update(self.root,[self.path],'cleanup')
        self.assertEqual(path.read_bytes(),before)
        with self.assertRaisesRegex(ValueError,'Missing target'):lifecycle.update(self.root,[self.path,'tasks/t1/missing.png'],'cleanup',include_protected=True)
        self.assertEqual(path.read_bytes(),before)
    def test_build_failure_rolls_back_registry(self):
        path=self.root/'.studio/project.json';before=path.read_bytes()
        with patch.object(dashboard,'build',side_effect=OSError('disk error')):
            with self.assertRaises(OSError):lifecycle.update(self.root,[self.path],'cleanup')
        self.assertEqual(path.read_bytes(),before)
        self.assertTrue((self.root/self.path).is_file())
    def test_inspection_is_read_only_and_reports_text_mentions(self):
        (self.root/'references/INDEX.md').write_text('See '+self.path)
        before=(self.root/'.studio/project.json').read_bytes()
        report=lifecycle.inspect(self.root,[self.path])
        self.assertIn('references/INDEX.md',report[0]['text_mentions'])
        self.assertEqual((self.root/'.studio/project.json').read_bytes(),before)

if __name__=='__main__':unittest.main()
