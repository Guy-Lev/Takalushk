from concurrent.futures import ThreadPoolExecutor
from .commons import org, db
import functools

from .models.schema import File, Test, HandledPull, TestCount, Repo
from .app_init import app

def needs_app_context(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        with app.app_context():
            return f(*args, **kwargs)

    return wrapper

class LearningTask(object):

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None

    def load_pulls(self, repo_name, direction='desc', stop_on_handled=True):
        if self.future and self.future.running():
            return "Error: The previous task is still running"

        self.future = self.executor.submit(self._do_load_pulls, repo_name, direction, stop_on_handled)
        return "Started task!"

    @needs_app_context
    def _do_load_pulls(self, repo_name, direction, stop_on_handled):
        repo_id = self._get_repo_id_from_name(repo_name)
        repo = org.get_repo(repo_name)
        for pull in repo.get_pulls('all', direction=direction):
            if self._is_pull_handled(pull, repo_id):
                if stop_on_handled:
                    break
                else:
                 continue
            files = self._get_files(pull, repo_id)
            tests = self._get_tests(pull)
            self._count_tests_for_files(files, tests)

    def _get_tests(self, pull):
        test_set = set()
        for comment in pull.get_issue_comments():
            c = comment.body
            if c.startswith("test ") and c.endswith(" please"):
                c = c[5:-7]
                tests = c.replace(",", "").split()
                test_type = "integration"
                if "cucumber" in tests:
                    test_type = "cucumber"
                for test_name in tests:
                    if test_name not in ["cucumber", "integration"]:
                        test = self._get_or_create_test(test_name, test_type)
                        test_set.add(test)

        return test_set

    def _get_files(self, pull, repo_name):
        files_set = set()
        for f in pull.get_files():
            file = self._get_or_create_file(f._filename.value, repo_name)
            files_set.add(file)
        return files_set

    def _count_tests_for_files(self, files, tests):
        if len(files) == 0 or len(tests) == 0:
            return
        for f in files:
            for t in tests:
                test_count = db.session.query(TestCount).filter_by(file_id=f.id, test_id=t.id).first()
                if not test_count:
                    test_count = TestCount(file_id=f.id, test_id=t.id, count=1)
                    db.session.add(test_count)
                else:
                    test_count.count = test_count.count + 1
                db.session.expire_on_commit = False
                db.session.commit()

    def _get_or_create_file(self, path, repo_id):
        file = db.session.query(File).filter_by(path=path, repo_id=repo_id).first()
        if not file:
            file = File(path=path, repo_id=repo_id)
            db.session.add(file)
            db.session.expire_on_commit = False
            db.session.commit()
        return file

    def _get_or_create_test(self, name, type):
        test = db.session.query(Test).filter_by(name=name, type=type).first()
        if not test:
            test = Test(name=name, type=type)
            db.session.add(test)
            db.session.expire_on_commit = False
            db.session.commit()
        return test

    def _is_pull_handled(self, pull, repo_id):
        handled_pull = db.session.query(HandledPull).filter_by(pull_id=pull.id, repo_id=repo_id).first()
        if not handled_pull:
            handled_pull = HandledPull(pull_id=pull.id, repo_id=repo_id)
            db.session.add(handled_pull)
            db.session.expire_on_commit = False
            db.session.commit()
            return False
        return True

    def _get_repo_id_from_name(self, repo_name):
        repo = db.session.query(Repo).filter_by(name=repo_name).first()
        if not repo:
            repo = Repo(name=repo_name)
            db.session.add(repo)
            db.session.expire_on_commit = False
            db.session.commit()
        return repo.id