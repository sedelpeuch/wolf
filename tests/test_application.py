import unittest

from wolf_core import application


class TestApplication(application.Application):
    def __init__(self):
        super().__init__()

    def job(self):
        self.set_status(application.Status.SUCCESS)


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.test_application = TestApplication()

    def test_initialisation(self):
        self.assertEqual(self.test_application.status, application.Status.WAITING)

    def test_status_property(self):
        self.assertEqual(self.test_application.status, application.Status.WAITING)

        # Check if the status is set to RUNNING normally not (property)
        self.test_application.__status = application.Status.RUNNING
        self.assertEqual(self.test_application.status, application.Status.WAITING)

    def test_status_setter(self):
        self.test_application.set_status(application.Status.WAITING)
        self.assertEqual(self.test_application.status, application.Status.WAITING)

        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            self.test_application.set_status("Truc")


if __name__ == '__main__':
    unittest.main()
