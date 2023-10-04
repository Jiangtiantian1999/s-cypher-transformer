import os
from unittest import TextTestRunner, defaultTestLoader, TestSuite

if __name__ == '__main__':
    current_path = os.path.dirname(__file__)
    match_suite = defaultTestLoader.discover(current_path, "test_match.py")
    where_suite = defaultTestLoader.discover(current_path, "test_where.py")
    return_suite = defaultTestLoader.discover(current_path, "test_return.py")
    unwind_suite = defaultTestLoader.discover(current_path, "test_unwind.py")
    call_suite = defaultTestLoader.discover(current_path, "test_call.py")
    with_suite = defaultTestLoader.discover(current_path, "test_with.py")
    time_window_suite = defaultTestLoader.discover(current_path, "test_time_window.py")
    create_suite = defaultTestLoader.discover(current_path, "test_create.py")
    set_suite = defaultTestLoader.discover(current_path, "test_set.py")
    stale_suite = defaultTestLoader.discover(current_path, "test_stale.py")
    remove_suite = defaultTestLoader.discover(current_path, "test_remove.py")
    delete_suite = defaultTestLoader.discover(current_path, "test_delete.py")

    suite = TestSuite()
    suite.addTest(match_suite)
    # suite.addTest(where_suite)
    # suite.addTest(return_suite)
    # suite.addTest(unwind_suite)
    # suite.addTest(call_suite)
    # suite.addTest(with_suite)
    # suite.addTest(time_window_suite)
    # suite.addTest(create_suite)
    # suite.addTest(set_suite)
    # suite.addTest(stale_suite)
    # suite.addTest(remove_suite)
    # suite.addTest(delete_suite)

    runner = TextTestRunner()
    runner.run(suite)
