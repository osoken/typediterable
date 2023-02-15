from dataclasses import dataclass
from inspect import Parameter, Signature
from typing import Any

import pytest
from pytest_mock import MockerFixture

import typediterable
from typediterable import core


class TwoArgumentDataType:
    def __init__(self, x: int, y: int):
        self._x = x
        self._y = y

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TwoArgumentDataType):
            return False
        return self.x == other.x and self.y == other.y


class KeywordOnlyArgumentDataType(TwoArgumentDataType):
    def __init__(self, *, x: int, y: int, text: str):
        super(KeywordOnlyArgumentDataType, self).__init__(x, y)
        self._text = text

    @property
    def text(self) -> str:
        return self._text

    def __eq__(self, other: Any) -> bool:
        if not super(KeywordOnlyArgumentDataType, self).__eq__(other):
            return False
        if not isinstance(other, KeywordOnlyArgumentDataType):
            return False
        return self.text == other.text


class TwoArgumentOneDefaultDataType(TwoArgumentDataType):
    def __init__(self, x: int, y: int = 0):
        super(TwoArgumentOneDefaultDataType, self).__init__(x, y)


@dataclass
class User:
    name: str
    id: int = 0


def test_iterate() -> None:
    actual = list(typediterable.TypedIterable[int](["122", "231", "0", "2", 2.3]))
    assert actual == [122, 231, 0, 2, 2]


def test_default_error_handling() -> None:
    actual = []
    with pytest.raises(Exception):
        for d in typediterable.TypedIterable[int](["123", "321", "1.23", "432"]):
            actual.append(d)
    assert actual == [123, 321]


def test_pass_error_handler() -> None:
    actual = []
    errors = []

    def handler(d: str, idx: int, err: Exception) -> None:
        errors.append((d, idx))

    for d in typediterable.TypedIterable[int](["123", "321", "1.23", "432"], on_error=handler):
        actual.append(d)
    assert actual == [123, 321, 432]
    assert errors == [("1.23", 2)]


def test_variable_length_arguments() -> None:
    actual = []
    for d in typediterable.VariableLengthArgumentTypedIterable[TwoArgumentDataType]([(10, 12), (-1, 3), (-3, -3)]):
        actual.append(d)

    assert actual == [TwoArgumentDataType(10, 12), TwoArgumentDataType(-1, 3), TwoArgumentDataType(-3, -3)]


def test_variable_length_keyword_arguments() -> None:
    actual = []
    for d in typediterable.VariableLengthKeywordArgumentTypedIterable[TwoArgumentDataType](
        [{"x": 10, "y": 12}, {"x": -1, "y": 3}, {"x": -3, "y": -3}, {"y": 0, "x": 0}]
    ):
        actual.append(d)

    assert actual == [
        TwoArgumentDataType(10, 12),
        TwoArgumentDataType(-1, 3),
        TwoArgumentDataType(-3, -3),
        TwoArgumentDataType(0, 0),
    ]


def test_keyword_only_arguments() -> None:
    actual = []
    for d in typediterable.VariableLengthKeywordArgumentTypedIterable[KeywordOnlyArgumentDataType](
        [
            {"x": 10, "y": 12, "text": "one"},
            {"x": -1, "y": 3, "text": "two"},
            {"x": -3, "y": -3, "text": "three"},
            {"y": 0, "x": 0, "text": "four"},
        ]
    ):
        actual.append(d)

    assert actual == [
        KeywordOnlyArgumentDataType(x=10, y=12, text="one"),
        KeywordOnlyArgumentDataType(x=-1, y=3, text="two"),
        KeywordOnlyArgumentDataType(x=-3, y=-3, text="three"),
        KeywordOnlyArgumentDataType(x=0, y=0, text="four"),
    ]


@pytest.mark.parametrize(
    ["argument_type", "patch"],
    [
        [core.ArgumentType.ONE_ARGUMENT, "typediterable.core.GenericTypedIterable"],
        [core.ArgumentType.VARIABLE_LENGTH_ARGUMENT, "typediterable.core.GenericVariableLengthArgumentTypedIterable"],
        [
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
            "typediterable.core.GenericVariableLengthArgumentKeywordTypedIterable",
        ],
    ],
)
def test_auto_argument_type(argument_type: core.ArgumentType, patch: str, mocker: MockerFixture) -> None:
    expected = mocker.patch(patch)
    signature = mocker.patch("typediterable.core.signature")
    _compute_signature_summary_by_signature = mocker.patch("typediterable.core._compute_signature_summary_by_signature")
    _compute_argument_type_by_signature_summary = mocker.patch(
        "typediterable.core._compute_argument_type_by_signature_summary"
    )
    _compute_argument_type_by_signature_summary.return_value = argument_type

    actual = typediterable.TypedIterable[TwoArgumentDataType]([])
    signature.assert_called_once_with(TwoArgumentDataType)
    _compute_signature_summary_by_signature.assert_called_once_with(signature.return_value)
    _compute_argument_type_by_signature_summary.assert_called_once_with(
        _compute_signature_summary_by_signature.return_value
    )
    assert actual == expected.__getitem__.return_value.return_value.return_value


def test_auto_adopt_keyword_only_argument() -> None:
    actual = []
    for d in typediterable.TypedIterable[KeywordOnlyArgumentDataType](
        [
            {"x": 10, "y": 12, "text": "one"},
            {"x": -1, "y": 3, "text": "two"},
            {"x": -3, "y": -3, "text": "three"},
            {"y": 0, "x": 0, "text": "four"},
        ]
    ):
        actual.append(d)

    assert actual == [
        KeywordOnlyArgumentDataType(x=10, y=12, text="one"),
        KeywordOnlyArgumentDataType(x=-1, y=3, text="two"),
        KeywordOnlyArgumentDataType(x=-3, y=-3, text="three"),
        KeywordOnlyArgumentDataType(x=0, y=0, text="four"),
    ]


@pytest.mark.parametrize(
    ["ss", "expected"],
    [
        [core.SignatureSummary(positional_only=1), core.ArgumentType.ONE_ARGUMENT],
        [core.SignatureSummary(positional_only=2), core.ArgumentType.VARIABLE_LENGTH_ARGUMENT],
        [core.SignatureSummary(positional_or_keyword=1), core.ArgumentType.ONE_ARGUMENT],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=1), core.ArgumentType.VARIABLE_LENGTH_ARGUMENT],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=1), core.ArgumentType.VARIABLE_LENGTH_ARGUMENT],
        [core.SignatureSummary(positional_or_keyword=2), core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=2), core.ArgumentType.VARIABLE_LENGTH_ARGUMENT],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=2), core.ArgumentType.VARIABLE_LENGTH_ARGUMENT],
        [core.SignatureSummary(keyword_only=1), core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT],
        [
            core.SignatureSummary(positional_or_keyword=1, keyword_only=1),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=2, keyword_only=1),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [core.SignatureSummary(keyword_only=2), core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT],
        [
            core.SignatureSummary(positional_or_keyword=1, keyword_only=2),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=2, keyword_only=2),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [core.SignatureSummary(var_positional=True), core.ArgumentType.VARIABLE_LENGTH_ARGUMENT],
        [core.SignatureSummary(positional_only=1, var_positional=True), core.ArgumentType.ONE_ARGUMENT],
        [core.SignatureSummary(positional_only=2, var_positional=True), core.ArgumentType.VARIABLE_LENGTH_ARGUMENT],
        [
            core.SignatureSummary(positional_or_keyword=1, var_positional=True),
            core.ArgumentType.ONE_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=1, positional_or_keyword=1, var_positional=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=2, positional_or_keyword=1, var_positional=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=2, var_positional=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=1, positional_or_keyword=2, var_positional=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=2, positional_or_keyword=2, var_positional=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(keyword_only=1, var_positional=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=1, keyword_only=1, var_positional=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=2, keyword_only=1, var_positional=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(keyword_only=2, var_positional=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=1, keyword_only=2, var_positional=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=2, keyword_only=2, var_positional=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [core.SignatureSummary(var_keyword=True), core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT],
        [core.SignatureSummary(positional_only=1, var_keyword=True), core.ArgumentType.ONE_ARGUMENT],
        [core.SignatureSummary(positional_only=2, var_keyword=True), core.ArgumentType.VARIABLE_LENGTH_ARGUMENT],
        [
            core.SignatureSummary(positional_or_keyword=1, var_keyword=True),
            core.ArgumentType.ONE_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=1, positional_or_keyword=1, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=2, positional_or_keyword=1, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=2, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=1, positional_or_keyword=2, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=2, positional_or_keyword=2, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [core.SignatureSummary(keyword_only=1, var_keyword=True), core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT],
        [
            core.SignatureSummary(positional_or_keyword=1, keyword_only=1, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=2, keyword_only=1, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [core.SignatureSummary(keyword_only=2, var_keyword=True), core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT],
        [
            core.SignatureSummary(positional_or_keyword=1, keyword_only=2, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=2, keyword_only=2, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [core.SignatureSummary(var_positional=True, var_keyword=True), core.ArgumentType.VARIABLE_LENGTH_ARGUMENT],
        [
            core.SignatureSummary(positional_only=1, var_positional=True, var_keyword=True),
            core.ArgumentType.ONE_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=2, var_positional=True, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=1, var_positional=True, var_keyword=True),
            core.ArgumentType.ONE_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=1, positional_or_keyword=1, var_positional=True, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=2, positional_or_keyword=1, var_positional=True, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=2, var_positional=True, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=1, positional_or_keyword=2, var_positional=True, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_only=2, positional_or_keyword=2, var_positional=True, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_ARGUMENT,
        ],
        [
            core.SignatureSummary(keyword_only=1, var_positional=True, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=1, keyword_only=1, var_positional=True, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=2, keyword_only=1, var_positional=True, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(keyword_only=2, var_positional=True, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=1, keyword_only=2, var_positional=True, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [
            core.SignatureSummary(positional_or_keyword=2, keyword_only=2, var_positional=True, var_keyword=True),
            core.ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT,
        ],
        [core.SignatureSummary(positional_or_keyword=core.IntRange(1, 2)), core.ArgumentType.K2O_FALLBACKABLE],
    ],
)
def test__compute_argument_type_by_signature_summary(ss: core.SignatureSummary, expected: core.ArgumentType) -> None:
    actual = core._compute_argument_type_by_signature_summary(ss)
    assert actual == expected


@pytest.mark.parametrize(
    ["ss"],
    [
        [core.SignatureSummary()],
        [core.SignatureSummary(positional_only=1, keyword_only=1)],
        [core.SignatureSummary(positional_only=2, keyword_only=1)],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=1, keyword_only=1)],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=1, keyword_only=1)],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=2, keyword_only=1)],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=2, keyword_only=1)],
        [core.SignatureSummary(positional_only=1, keyword_only=2)],
        [core.SignatureSummary(positional_only=2, keyword_only=2)],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=1, keyword_only=2)],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=1, keyword_only=2)],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=2, keyword_only=2)],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=2, keyword_only=2)],
        [core.SignatureSummary(positional_only=1, keyword_only=1, var_positional=True)],
        [core.SignatureSummary(positional_only=2, keyword_only=1, var_positional=True)],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=1, keyword_only=1, var_positional=True)],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=1, keyword_only=1, var_positional=True)],
        [
            core.SignatureSummary(positional_only=1, positional_or_keyword=2, keyword_only=1, var_positional=True),
        ],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=2, keyword_only=1, var_positional=True)],
        [core.SignatureSummary(positional_only=1, keyword_only=2, var_positional=True)],
        [core.SignatureSummary(positional_only=2, keyword_only=2, var_positional=True)],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=1, keyword_only=2, var_positional=True)],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=1, keyword_only=2, var_positional=True)],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=2, keyword_only=2, var_positional=True)],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=2, keyword_only=2, var_positional=True)],
        [core.SignatureSummary(positional_only=1, keyword_only=1, var_keyword=True)],
        [core.SignatureSummary(positional_only=2, keyword_only=1, var_keyword=True)],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=1, keyword_only=1, var_keyword=True)],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=1, keyword_only=1, var_keyword=True)],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=2, keyword_only=1, var_keyword=True)],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=2, keyword_only=1, var_keyword=True)],
        [core.SignatureSummary(positional_only=1, keyword_only=2, var_keyword=True)],
        [core.SignatureSummary(positional_only=2, keyword_only=2, var_keyword=True)],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=1, keyword_only=2, var_keyword=True)],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=1, keyword_only=2, var_keyword=True)],
        [core.SignatureSummary(positional_only=1, positional_or_keyword=2, keyword_only=2, var_keyword=True)],
        [core.SignatureSummary(positional_only=2, positional_or_keyword=2, keyword_only=2, var_keyword=True)],
        [core.SignatureSummary(positional_only=1, keyword_only=1, var_positional=True, var_keyword=True)],
        [core.SignatureSummary(positional_only=2, keyword_only=1, var_positional=True, var_keyword=True)],
        [
            core.SignatureSummary(
                positional_only=1, positional_or_keyword=1, keyword_only=1, var_positional=True, var_keyword=True
            )
        ],
        [
            core.SignatureSummary(
                positional_only=2, positional_or_keyword=1, keyword_only=1, var_positional=True, var_keyword=True
            )
        ],
        [
            core.SignatureSummary(
                positional_only=1, positional_or_keyword=2, keyword_only=1, var_positional=True, var_keyword=True
            )
        ],
        [
            core.SignatureSummary(
                positional_only=2, positional_or_keyword=2, keyword_only=1, var_positional=True, var_keyword=True
            )
        ],
        [core.SignatureSummary(positional_only=1, keyword_only=2, var_positional=True, var_keyword=True)],
        [core.SignatureSummary(positional_only=2, keyword_only=2, var_positional=True, var_keyword=True)],
        [
            core.SignatureSummary(
                positional_only=1, positional_or_keyword=1, keyword_only=2, var_positional=True, var_keyword=True
            )
        ],
        [
            core.SignatureSummary(
                positional_only=2, positional_or_keyword=1, keyword_only=2, var_positional=True, var_keyword=True
            )
        ],
        [
            core.SignatureSummary(
                positional_only=1, positional_or_keyword=2, keyword_only=2, var_positional=True, var_keyword=True
            )
        ],
        [
            core.SignatureSummary(
                positional_only=2, positional_or_keyword=2, keyword_only=2, var_positional=True, var_keyword=True
            )
        ],
    ],
)
def test__compute_argument_type_by_signature_summary_error_cases(ss: core.SignatureSummary) -> None:
    with pytest.raises(ValueError):
        _ = core._compute_argument_type_by_signature_summary(ss)


@pytest.mark.parametrize(
    ["sig", "expected"],
    [
        [
            Signature(parameters=(Parameter(name="id", kind=Parameter.POSITIONAL_ONLY, annotation=str),)),
            core.SignatureSummary(
                positional_only=1, positional_or_keyword=0, var_positional=False, keyword_only=0, var_keyword=False
            ),
        ],
        [
            Signature(
                parameters=(
                    Parameter(name="id", kind=Parameter.POSITIONAL_ONLY, annotation=str),
                    Parameter(name="name", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
                    Parameter(name="email", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
                )
            ),
            core.SignatureSummary(
                positional_only=1, positional_or_keyword=2, var_positional=False, keyword_only=0, var_keyword=False
            ),
        ],
        [
            Signature(
                parameters=(
                    Parameter(name="id", kind=Parameter.POSITIONAL_ONLY, annotation=str),
                    Parameter(name="name", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
                    Parameter(name="email", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
                    Parameter(name="args", kind=Parameter.VAR_POSITIONAL),
                )
            ),
            core.SignatureSummary(
                positional_only=1, positional_or_keyword=2, var_positional=True, keyword_only=0, var_keyword=False
            ),
        ],
        [
            Signature(
                parameters=(
                    Parameter(name="id", kind=Parameter.POSITIONAL_ONLY, annotation=str),
                    Parameter(name="name", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
                    Parameter(name="email", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
                    Parameter(name="args", kind=Parameter.VAR_POSITIONAL),
                    Parameter(name="age", kind=Parameter.KEYWORD_ONLY, annotation=int),
                )
            ),
            core.SignatureSummary(
                positional_only=1, positional_or_keyword=2, var_positional=True, keyword_only=1, var_keyword=False
            ),
        ],
        [
            Signature(
                parameters=(
                    Parameter(name="id", kind=Parameter.POSITIONAL_ONLY, annotation=str),
                    Parameter(name="name", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
                    Parameter(name="email", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
                    Parameter(name="args", kind=Parameter.VAR_POSITIONAL),
                    Parameter(name="age", kind=Parameter.KEYWORD_ONLY, annotation=int),
                    Parameter(name="kwargs", kind=Parameter.VAR_KEYWORD),
                )
            ),
            core.SignatureSummary(
                positional_only=1, positional_or_keyword=2, var_positional=True, keyword_only=1, var_keyword=True
            ),
        ],
        [
            Signature(
                parameters=(
                    Parameter(name="id", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
                    Parameter(name="name", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str, default="john"),
                )
            ),
            core.SignatureSummary(positional_or_keyword=core.IntRange(1, 2)),
        ],
    ],
)
def test__compute_signature_summary_by_signature(sig: Signature, expected: core.SignatureSummary) -> None:
    actual = core._compute_signature_summary_by_signature(sig)
    assert actual == expected


def test_type_with_default() -> None:
    raw_data = [10]
    expected = [TwoArgumentOneDefaultDataType(10)]

    assert list(typediterable.TypedIterable[TwoArgumentOneDefaultDataType](raw_data)) == expected


def test_k2o_fallbackable_typing_itrerable() -> None:
    from typediterable.core import K2OFallbackableTypedIterable

    raw_data = [10, {"x": 1, "y": 2}]
    expected = [TwoArgumentOneDefaultDataType(10), TwoArgumentOneDefaultDataType(x=1, y=2)]

    assert list(K2OFallbackableTypedIterable[TwoArgumentOneDefaultDataType](raw_data)) == expected


def test_adoptive_cast() -> None:
    raw_data = ["aa", ("bb", 10), {"id": 20, "name": "cc"}]
    expected = [User(id=0, name="aa"), User(id=10, name="bb"), User(id=20, name="cc")]
    assert list(typediterable.AdaptiveTypedIterable[User](raw_data)) == expected
