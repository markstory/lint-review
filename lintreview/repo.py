import lintreview.github as github
import lintreview.git as git

class GithubRepository(object):
    """Abstracting wrapper for the
    various interactions we have with github.

    This will make swapping in other hosting systems
    a tiny bit easier in the future.
    """

    def __init__(self, config, user, repo_name):
        self.config = config
        self.user = user
        self.repo_name = repo_name

    def repository(self):
        self.repo = github.get_repository(
            self.config,
            self.user,
            self.repo_name)
        return self.repo

    def pull_request(self, number):
        pull = self.repository().pull_request(number)
        return GithubPullRequest(pull)


class GithubPullRequest(object):
    """Abstract the underlying github models.
    This makes other code simpler, and enables
    the ability to add other hosting services later.
    """

    def __init__(self, pull_request):
        self.pull = pull_request

    @property
    def number(self):
        return self.pull.number

    @property
    def is_private(self):
        data = self.pull.as_dict()
        return data['head']['repo']['private']

    @property
    def head(self):
        data = self.pull.as_dict()
        return data['head']['sha']

    @property
    def clone_url(self):
        data = self.pull.as_dict()
        return data['head']['repo']['clone_url']

    @property
    def target_branch(self):
        data = self.pull.as_dict()
        return data['base']['ref']

    def commits(self):
        return self.pull.commits()

    def files(self):
        return list(self.pull.files())
