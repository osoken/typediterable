import pytest

import typingiterable


def test_iterate() -> None:
    actual = list(typingiterable.TypingIterable[int](["122", "231", "0", "2", 2.3]))
    assert actual == [122, 231, 0, 2, 2]


def test_default_error_handling() -> None:
    actual = []
    with pytest.raises(Exception):
        for d in typingiterable.TypingIterable[int](["123", "321", "1.23", "432"]):
            actual.append(d)
    assert actual == [123, 321]


def test_pass_error_handler() -> None:
    actual = []
    errors = []

    def handler(d: str, idx: int, err: Exception) -> None:
        errors.append((d, idx))

    for d in typingiterable.TypingIterable[int](["123", "321", "1.23", "432"], on_error=handler):
        actual.append(d)
    assert actual == [123, 321, 432]
    assert errors == [("1.23", 2)]
