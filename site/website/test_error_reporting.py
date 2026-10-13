from django.test import SimpleTestCase

from bugsnag.configuration import Configuration

from website.error_reporting import BUGSNAG_MIDDLEWARE, bugsnag_config, with_bugsnag_middleware


def configured(**options):
    configuration = Configuration()
    configuration.configure(**bugsnag_config(project_root="/srv", **options))
    return configuration


class BugsnagToggleTests(SimpleTestCase):
    def test_enabled_in_production_notifies(self):
        configuration = configured(enabled=True, api_key="a" * 32, debug=False)
        self.assertEqual(configuration.release_stage, "production")
        self.assertTrue(configuration.should_notify())

    def test_disabled_sends_nothing(self):
        configuration = configured(enabled=False, api_key="a" * 32, debug=False)
        self.assertFalse(configuration.should_notify())

    def test_enabled_in_development_notifies_as_development(self):
        configuration = configured(enabled=True, api_key="a" * 32, debug=True)
        self.assertEqual(configuration.release_stage, "development")
        self.assertTrue(configuration.should_notify())

    def test_missing_key_is_not_an_error(self):
        self.assertIsNone(bugsnag_config(enabled=False, api_key="", debug=True, project_root="/srv")["api_key"])

    def test_middleware_only_when_enabled(self):
        middleware = ["corsheaders.middleware.CorsMiddleware"]
        self.assertEqual(with_bugsnag_middleware(middleware, enabled=True)[0], BUGSNAG_MIDDLEWARE)
        self.assertNotIn(BUGSNAG_MIDDLEWARE, with_bugsnag_middleware(middleware, enabled=False))
        self.assertEqual(middleware, ["corsheaders.middleware.CorsMiddleware"])
