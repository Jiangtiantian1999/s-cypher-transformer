import os
from unittest import TextTestRunner, defaultTestLoader, TestSuite

if __name__ == '__main__':
    current_path = os.path.dirname(__file__)
    match_suite = defaultTestLoader.discover(current_path, "test_*.py")

    suite = TestSuite()
    suite.addTest(match_suite)

    runner = TextTestRunner()
    runner.run(suite)
