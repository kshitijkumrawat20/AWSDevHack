"""Compatibility layer for hypothesis property testing.

If hypothesis is installed, uses real hypothesis engine.
If hypothesis is not installed, runs property assertions across representative samples.
"""

from __future__ import annotations

try:
    from hypothesis import given, strategies as st
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False

    class _MockStrategies:
        def integers(self, min_value: int = 1, max_value: int = 10):
            return list(range(min_value, min(min_value + 5, max_value + 1)))

        def lists(self, elements, min_size: int = 1, max_size: int = 5):
            return [[1, 2], [1, 2, 3], [2, 4, 5], [1, 5, 6]]

        def sampled_from(self, items):
            return items

        def text(self, min_size: int = 1, max_size: int = 50):
            return [
                "parents visiting tomorrow",
                "wellness low-sodium",
                "warm ambient lighting",
                "tea and herbal supplements",
                "unexpected visitor at door",
            ]

        def one_of(self, *strategies):
            return [1, 42, "req_101", "req_alpha"]

    st = _MockStrategies()  # type: ignore

    def given(*strategy_args, **kwargs):
        def decorator(fn):
            def wrapper(*args, **kw):
                if not strategy_args:
                    return fn(*args, **kw)
                sample = strategy_args[0]
                if isinstance(sample, list):
                    for item in sample:
                        fn(item)
                else:
                    fn(sample)
            return wrapper
        return decorator
