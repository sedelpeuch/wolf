import time
import unittest

from wolf_core import runner, application


class TestApplication(application.Application):
    def __init__(self):
        super().__init__()

    def job(self):
        time.sleep(1)
        self.set_status(application.Status.SUCCESS)
        time.sleep(0.5)


class EmptyApplication(application.Application):
    def __init__(self):
        super().__init__()


class TestApplicationBad(application.Application):
    def __init__(self):
        super().__init__()

    def job(self):
        self.status = "TEST"

    def run(self):
        self.job()


class TestRunner(unittest.TestCase):
    def setUp(self) -> None:
        self.test_runner = runner.Runner(debug=True)

    def test_initialisation(self):
        self.assertEqual(self.test_runner._applications, [])
        self.assertEqual(self.test_runner._Runner__debug, True)

    def test_setup_logger(self):
        self.test_runner._Runner__setup_logger()
        self.assertNotEqual(self.test_runner.logger, None)

    def test_load_applications(self):
        self.test_runner._Runner__load_applications()
        self.assertNotEqual(self.test_runner._applications, [])
        self.assertNotEqual(self.test_runner._applications[0].logger, None)

    def test_get_status(self):
        self.test_runner._Runner__load_applications()
        self.test_runner._Runner__get_status(self.test_runner._applications[0])
        self.assertNotEqual(self.test_runner._Runner__app_health["TestApplication"]["status"],
                            {application.Status.WAITING})

    def test_run(self):
        self.test_runner.run()

    def test_is_method_overridden(self):
        self.assertFalse(self.test_runner.is_method_overridden(TestApplication, "run"))
        self.assertTrue(self.test_runner.is_method_overridden(TestApplicationBad, "run"))


if __name__ == '__main__':
    unittest.main()
