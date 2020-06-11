from unittest import TestCase

from lintreview.config import build_review_config, get_lintrc_defaults
from lintreview.config import load_config, ReviewConfig

sample_ini = """
[files]
ignore = test/CodeStandards/test/**
    vendor/**

[tools]
linters = phpcs, pep8, jshint

[tool_jshint]
config = ./jshint.json

[tool_phpcs]
standard = test/CodeStandards
config = test/phpcs.xml
"""

defaults_ini = """
[tool_jshint]
config = /etc/jshint.json
"""

simple_ini = """
[tools]
linters = jshint
"""

review_ini = """
[tools]
linters = jshint

[review]
summary_comment_threshold = 25
fail_on_comments = False
apply_label_on_pass = lint ok
"""

fixer_ini = """
[tools]
linters = phps

[fixers]
enable = True
workflow = pull_request
"""

bad_ini = """
[herp]
derp=derplily
"""

# Simulate the application config
app_config = {
    'SUMMARY_THRESHOLD': 100,
    'OK_LABEL': 'no lint',
    'PULLREQUEST_STATUS': True
}


class ReviewConfigTest(TestCase):

    @staticmethod
    def test_load_config():
        res = load_config()
        assert res['GITHUB_URL'].endswith, 'Exists and is stringy'

    @staticmethod
    def test_get_lintrc_defaults():
        config = load_config()
        res = get_lintrc_defaults(config)
        assert res is None

    def test_build_review_config(self):
        config = build_review_config(sample_ini, {})
        assert isinstance(config, ReviewConfig)
        self.assertEqual(3, len(config.linters()))

    def test_linter_listing_bad(self):
        config = build_review_config(bad_ini)
        res = config.linters()
        self.assertEqual(res, [])

    def test_linter_listing(self):
        config = build_review_config(sample_ini)
        res = config.linters()
        expected = ['phpcs', 'pep8', 'jshint']
        self.assertEqual(sorted(res), sorted(expected))

    def test_linter_config_bad(self):
        config = build_review_config(bad_ini)
        res = config.linter_config('phpcs')
        self.assertEqual(res, {})

    def test_linter_config(self):
        config = build_review_config(sample_ini)
        res = config.linter_config('phpcs')
        expected = {
            'standard': 'test/CodeStandards',
            'config': 'test/phpcs.xml'
        }
        self.assertEqual(res, expected)

        res = config.linter_config('not there')
        self.assertEqual(res, {})

    def test_ignore_patterns(self):
        config = build_review_config(sample_ini)
        res = config.ignore_patterns()
        expected = ['test/CodeStandards/test/**', 'vendor/**']
        self.assertEqual(res, expected)

    def test_ignore_patterns_missing(self):
        config = ReviewConfig()
        res = config.ignore_patterns()
        self.assertEqual(res, [])

    def test_load_ini__override(self):
        config = ReviewConfig()
        config.load_ini(defaults_ini)
        config.load_ini(sample_ini)
        res = config.linter_config('jshint')
        expected = {
            'config': './jshint.json',
        }
        self.assertEqual(res, expected)

    def test_load_ini__multiple_merges_settings(self):
        config = ReviewConfig()
        config.load_ini(defaults_ini)
        config.load_ini(simple_ini)
        res = config.linter_config('jshint')
        expected = {
            'config': '/etc/jshint.json',
        }
        self.assertEqual(res, expected)

    def test_fixers_enabled(self):
        config = build_review_config(sample_ini)
        self.assertEqual(False, config.fixers_enabled())

        config = build_review_config(fixer_ini)
        self.assertEqual(True, config.fixers_enabled())

    def test_fixer_workflow(self):
        config = build_review_config(sample_ini)
        self.assertEqual('commit', config.fixer_workflow())

        config = build_review_config(fixer_ini)
        self.assertEqual('pull_request', config.fixer_workflow())

    def test_getitem(self):
        config = build_review_config(simple_ini, app_config)
        self.assertEqual(app_config['SUMMARY_THRESHOLD'],
                         config['SUMMARY_THRESHOLD'])

    def test_getitem__error(self):
        config = build_review_config(simple_ini, app_config)
        with self.assertRaises(KeyError):
            config['UNKNOWN']

    def test_get(self):
        config = build_review_config(simple_ini, app_config)
        self.assertEqual(app_config['SUMMARY_THRESHOLD'],
                         config.get('SUMMARY_THRESHOLD'))
        self.assertEqual(None, config.get('unknown'))
        self.assertEqual('default', config.get('unknown', 'default'))

    def test_summary_threshold__undefined(self):
        config = build_review_config(simple_ini)
        self.assertEqual(None, config.summary_threshold())

    def test_summary_threshold__app_config(self):
        config = build_review_config(simple_ini, app_config)
        self.assertEqual(app_config['SUMMARY_THRESHOLD'],
                         config.summary_threshold())

    def test_summary_threshold__job_config(self):
        config = build_review_config(review_ini, app_config)
        self.assertEqual(25, config.summary_threshold())

    def test_passed_review_label__undefined(self):
        config = build_review_config(simple_ini)
        self.assertEqual(None, config.passed_review_label())

    def test_passed_review_label__app_config(self):
        config = build_review_config(simple_ini, app_config)
        self.assertEqual('no lint', config.passed_review_label())

    def test_passed_review_label__job_config(self):
        config = build_review_config(review_ini, app_config)
        self.assertEqual('lint ok', config.passed_review_label())

    def test_failed_review_status__undefined(self):
        config = build_review_config(simple_ini)
        self.assertEqual('failure', config.failed_review_status())

    def test_failed_review_status__app_config(self):
        config = build_review_config(simple_ini, {'PULLREQUEST_STATUS': True})
        self.assertEqual('failure', config.failed_review_status())

        config = build_review_config(simple_ini, {'PULLREQUEST_STATUS': False})
        self.assertEqual('success', config.failed_review_status())

    def test_failed_review_status__job_config(self):
        config = build_review_config(review_ini, app_config)
        self.assertEqual('success', config.failed_review_status())

        ini = "[review]\nfail_on_comments = true"
        config = build_review_config(ini, app_config)
        self.assertEqual('failure', config.failed_review_status())
