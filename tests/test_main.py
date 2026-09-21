import inspect

from app.main import main


def test_main_is_async():
    """
    Tripzy's CLI entry point should remain asynchronous because
    the conversation workflow runs async agents and services.
    """

    assert inspect.iscoroutinefunction(main)