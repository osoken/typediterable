import sys
from dataclasses import dataclass
from inspect import Parameter, Signature, signature

if sys.version_info < (3, 9):
    from typing import Callable, Iterable, Mapping
else:
    from collections.abc import Callable, Iterable, Mapping

from enum import Enum
from typing import Any, Generic, Optional, Tuple, Type, TypeVar, Union

T = TypeVar("T")


class ArgumentType(str, Enum):
    AUTO = "AUTO"
    ADAPTIVE = "ADAPTIVE"
    ONE_ARGUMENT = "ONE_ARGUMENT"
    VARIABLE_LENGTH_ARGUMENT = "VARIABLE_LENGTH_ARGUMENT"
    VARIABLE_LENGTH_KEYWORD_ARGUMENT = "VARIABLE_LENGTH_KEYWORD_ARGUMENT"
    K2O_FALLBACKABLE = "K2O_FALLBACKABLE"


class IntRange:
    def __init__(self, imin: int, imax: int):
        self._imin = imin
        self._imax = imax

    def __add__(self, i: Union[int, "IntRange"]) -> "IntRange":
        res = self.__class__(self.min, self.max)
        res += i
        return res

    def __iadd__(self, i: Union[int, "IntRange"]) -> "IntRange":
        if isinstance(i, int):
            self._imin += 1
            self._imax += 1
        elif isinstance(i, IntRange):
            self._imin += i.min
            self._imax += i.max
        else:
            raise TypeError(type(i))
        return self

    def __getitem__(self, idx: int) -> int:
        if idx < 0 or 2 <= idx:
            raise IndexError(idx)
        if idx == 0:
            return self.min
        return self.max

    @property
    def min(self) -> int:
        return self._imin

    @property
    def max(self) -> int:
        return self._imax

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, IntRange):
            return self.min == other.min and self.max == other.max
        return False


def max_num(x: Union[int, IntRange]) -> int:
    if isinstance(x, int):
        return x
    return x.max


def min_num(x: Union[int, IntRange]) -> int:
    if isinstance(x, int):
        return x
    return x.min


@dataclass(frozen=True)
class SignatureSummary:
    positional_only: Union[int, IntRange] = 0
    positional_or_keyword: Union[int, IntRange] = 0
    var_positional: bool = False
    keyword_only: Union[int, IntRange] = 0
    var_keyword: bool = False


def _compute_signature_summary_by_signature(s: Signature) -> SignatureSummary:
    positional_only: Union[int, IntRange] = 0
    positional_or_keyword: Union[int, IntRange] = 0
    var_positional = False
    keyword_only: Union[int, IntRange] = 0
    var_keyword = False
    for p in s.parameters.values():
        if p.kind == Parameter.POSITIONAL_ONLY:
            if p.default != Parameter.empty:
                if isinstance(positional_only, int):
                    positional_only = IntRange(positional_only, positional_only + 1)
                else:
                    positional_only += IntRange(0, 1)
            else:
                positional_only += 1
        elif p.kind == Parameter.POSITIONAL_OR_KEYWORD:
            if p.default != Parameter.empty:
                if isinstance(positional_or_keyword, int):
                    positional_or_keyword = IntRange(positional_or_keyword, positional_or_keyword + 1)
                else:
                    positional_or_keyword += IntRange(0, 1)
            else:
                positional_or_keyword += 1
        elif p.kind == Parameter.KEYWORD_ONLY:
            if p.default != Parameter.empty:
                if isinstance(keyword_only, int):
                    keyword_only = IntRange(keyword_only, keyword_only + 1)
                else:
                    keyword_only += IntRange(0, 1)
            else:
                keyword_only += 1
        elif p.kind == Parameter.VAR_POSITIONAL:
            var_positional = True
        elif p.kind == Parameter.VAR_KEYWORD:
            var_keyword = True
    return SignatureSummary(
        positional_only=positional_only,
        positional_or_keyword=positional_or_keyword,
        var_positional=var_positional,
        keyword_only=keyword_only,
        var_keyword=var_keyword,
    )


def _compute_argument_type_by_signature_summary(ss: SignatureSummary) -> ArgumentType:
    if max_num(ss.positional_only) > 0 and max_num(ss.keyword_only) > 0:
        raise ValueError("signature not supported")
    if max_num(ss.positional_only) == 0 and max_num(ss.keyword_only) == 0 and max_num(ss.positional_or_keyword) == 0:
        if ss.var_positional:
            return ArgumentType.VARIABLE_LENGTH_ARGUMENT
        elif ss.var_keyword:
            return ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT
        raise ValueError("signature not supported")
    if min_num(ss.keyword_only) > 0:
        return ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT
    if max_num(ss.positional_only) + max_num(ss.positional_or_keyword) == 1:
        return ArgumentType.ONE_ARGUMENT
    if (
        max_num(ss.positional_only) + max_num(ss.positional_or_keyword) > 1
        and min_num(ss.positional_only) >= 1
        or ss.var_positional
        and not ss.var_keyword
    ):
        return ArgumentType.VARIABLE_LENGTH_ARGUMENT
    if min_num(ss.positional_only) + min_num(ss.positional_or_keyword) <= 1:
        return ArgumentType.K2O_FALLBACKABLE
    return ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT


class GenericTypedIterable(Generic[T]):
    def __init__(self, t: Type[T]):
        self._t = t

    def _cast(self, d: Any) -> T:
        return self._t(d)  # type: ignore [call-arg]

    def __call__(
        self, it: Iterable[Any], on_error: Optional[Callable[[Any, int, Exception], None]] = None
    ) -> Iterable[T]:
        if on_error is not None:
            for i, d in enumerate(it):
                try:
                    yield self._cast(d)
                except Exception as e:
                    on_error(d, i, e)
        else:
            for d in it:
                yield self._cast(d)


class GenericVariableLengthArgumentTypedIterable(Generic[T], GenericTypedIterable[T]):
    def _cast(self, d: Any) -> T:
        return self._t(*d)


class GenericVariableLengthArgumentKeywordTypedIterable(Generic[T], GenericTypedIterable[T]):
    def _cast(self, d: Any) -> T:
        return self._t(**d)


class GenericK2OFallbackableTypedIterable(Generic[T], GenericTypedIterable[T]):
    def _cast(self, d: Any) -> T:
        try:
            return self._t(**d)
        except TypeError:
            ...
        return self._t(d)  # type: ignore [call-arg]


class GenericAdaptiveTypedIterable(Generic[T], GenericTypedIterable[T]):
    def _cast(self, d: Any) -> T:
        if isinstance(d, Iterable) and not isinstance(d, (str, bytes)):
            if isinstance(d, Mapping):
                try:
                    return self._t(**d)
                except TypeError:
                    ...
            else:
                try:
                    return self._t(*d)
                except TypeError:
                    ...
        return self._t(d)  # type: ignore [call-arg]


class GenericTypedIterableFactory:
    def __init__(self, argument_type: ArgumentType = ArgumentType.ONE_ARGUMENT):
        self._argument_type = argument_type

    def __getitem__(self, t: Type[T]) -> GenericTypedIterable[T]:
        at = self._argument_type
        if at == ArgumentType.AUTO:
            try:
                sig = signature(t)
            except ValueError:
                return GenericTypedIterable[T](t)
            at = _compute_argument_type_by_signature_summary(_compute_signature_summary_by_signature(sig))
        if at == ArgumentType.VARIABLE_LENGTH_ARGUMENT:
            return GenericVariableLengthArgumentTypedIterable[T](t)
        elif at == ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT:
            return GenericVariableLengthArgumentKeywordTypedIterable[T](t)
        elif at == ArgumentType.K2O_FALLBACKABLE:
            return GenericK2OFallbackableTypedIterable[T](t)
        elif at == ArgumentType.ADAPTIVE:
            return GenericAdaptiveTypedIterable[T](t)
        return GenericTypedIterable[T](t)


TypedIterable = GenericTypedIterableFactory(argument_type=ArgumentType.AUTO)
OneArgumentTypedIterable = GenericTypedIterableFactory(argument_type=ArgumentType.ONE_ARGUMENT)
VariableLengthArgumentTypedIterable = GenericTypedIterableFactory(argument_type=ArgumentType.VARIABLE_LENGTH_ARGUMENT)
VariableLengthKeywordArgumentTypedIterable = GenericTypedIterableFactory(
    argument_type=ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT
)
VarArgTypedIterable = VariableLengthArgumentTypedIterable
KwArgTypedIterable = VariableLengthKeywordArgumentTypedIterable
K2OFallbackableTypedIterable = GenericTypedIterableFactory(argument_type=ArgumentType.K2O_FALLBACKABLE)
AdaptiveTypedIterable = GenericTypedIterableFactory(argument_type=ArgumentType.ADAPTIVE)
