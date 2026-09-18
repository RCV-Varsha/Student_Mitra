"""Record automated fixture regression outcomes without contacting an AI provider."""
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.test.runner import DiscoverRunner
from study.models import Evaluation

class RecordingRunner(DiscoverRunner):
    def run_suite(self,suite,**kwargs):
        self.recorded=super().run_suite(suite,**kwargs)
        return self.recorded

class Command(BaseCommand):
    help='Run deterministic provider-fixture regression evaluations in an isolated test database'
    def add_arguments(self,p):p.add_argument('--output',default='docs/regression-results.json')
    def handle(self,*args,**options):
        runner=RecordingRunner(verbosity=1,interactive=False)
        failures=runner.run_tests(['study.test_should'])
        result=runner.recorded
        failed=[{'name':str(test),'passed':False,'detail':'Regression assertion failed; see test log.'} for test,_ in result.failures+result.errors]
        summary={'mode':'mocked regression; no live provider calls','total':result.testsRun,'passed':result.testsRun-len(failed),'results':failed or [{'name':'Should Have regression suite','passed':True,'detail':f'{result.testsRun} deterministic tests passed; provider responses are fixtures.'}]}
        Evaluation.objects.create(mode='regression',total=summary['total'],passed=summary['passed'],results=summary['results'])
        Path(options['output']).write_text(json.dumps(summary,indent=2),encoding='utf-8')
        if failures:raise CommandError('Regression evaluation failed')
