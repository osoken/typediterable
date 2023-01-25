import sys
from dataclasses import dataclass
from inspect import Parameter, Signature, signature

if sys.version_info < (3, 9):
    from typing import Callable, Iterable
else:
    from collections.abc import Callable, Iterable

from enum import Enum
from typing import Any, Generic, Optional, Tuple, Type, TypeVar, Union

T = TypeVar("T")


class ArgumentType(str, Enum):
    AUTO = "AUTO"
    ONE_ARGUMENT = "ONE_ARGUMENT"
    VARIABLE_LENGTH_ARGUMENT = "VARIABLE_LENGTH_ARGUMENT"
    VARIABLE_LENGTH_KEYWORD_ARGUMENT = "VARIABLE_LENGTH_KEYWORD_ARGUMENT"


IntRange = Tuple[int, int]


@dataclass(frozen=True)
class SignatureSummary:
    positional_only: Union[int, IntRange] = 0
    positional_or_keyword: Union[int, IntRange] = 0
    var_positional: bool = False
    keyword_only: Union[int, IntRange] = 0
    var_keyword: bool = False


def _compute_signature_summary_by_signature(s: Signature) -> SignatureSummary:
    positional_only = 0
    positional_or_keyword = 0
    var_positional = False
    keyword_only = 0
    var_keyword = False
    for p in s.parameters.values():
        if p.kind == Parameter.POSITIONAL_ONLY:
            positional_only += 1
        elif p.kind == Parameter.POSITIONAL_OR_KEYWORD:
            positional_or_keyword += 1
        elif p.kind == Parameter.KEYWORD_ONLY:
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
    if ss.positional_only > 0 and ss.keyword_only > 0:
        raise ValueError("signature not supported")
    if ss.positional_only == 0 and ss.keyword_only == 0 and ss.positional_or_keyword == 0:
        if ss.var_positional:
            return ArgumentType.VARIABLE_LENGTH_ARGUMENT
        elif ss.var_keyword:
            return ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT
        raise ValueError("signature not supported")
    if ss.keyword_only > 0:
        return ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT
    if ss.positional_only + ss.positional_or_keyword == 1:
        return ArgumentType.ONE_ARGUMENT
    if (
        ss.positional_only + ss.positional_or_keyword > 1
        and ss.positional_only >= 1
        or ss.var_positional
        and not ss.var_keyword
    ):
        return ArgumentType.VARIABLE_LENGTH_ARGUMENT
    return ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT


class GenericTypingIterable(Generic[T]):
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


class GenericVariableLengthArgumentTypingIterable(Generic[T], GenericTypingIterable[T]):
    def _cast(self, d: Any) -> T:
        return self._t(*d)


class GenericVariableLengthArgumentKeywordTypingIterable(Generic[T], GenericTypingIterable[T]):
    def _cast(self, d: Any) -> T:
        return self._t(**d)


class GenericK2OFallbackableTypingIterable(Generic[T], GenericTypingIterable[T]):
    def _cast(self, d: Any) -> T:
        try:
            return self._t(**d)
        except TypeError:
            ...
        return self._t(d)


class GenericTypingIterableFactory:
    def __init__(self, argument_type: ArgumentType = ArgumentType.ONE_ARGUMENT):
        self._argument_type = argument_type

    def __getitem__(self, t: Type[T]) -> GenericTypingIterable[T]:
        at = self._argument_type
        if at == ArgumentType.AUTO:
            try:
                sig = signature(t)
            except ValueError:
                return GenericTypingIterable[T](t)
            at = _compute_argument_type_by_signature_summary(_compute_signature_summary_by_signature(sig))
        if at == ArgumentType.VARIABLE_LENGTH_ARGUMENT:
            return GenericVariableLengthArgumentTypingIterable[T](t)
        elif at == ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT:
            return GenericVariableLengthArgumentKeywordTypingIterable[T](t)
        return GenericTypingIterable[T](t)


TypingIterable = GenericTypingIterableFactory(argument_type=ArgumentType.AUTO)
OneArgumentTypingIterable = GenericTypingIterableFactory(argument_type=ArgumentType.ONE_ARGUMENT)
VariableLengthArgumentTypingIterable = GenericTypingIterableFactory(argument_type=ArgumentType.VARIABLE_LENGTH_ARGUMENT)
VariableLengthKeywordArgumentTypingIterable = GenericTypingIterableFactory(
    argument_type=ArgumentType.VARIABLE_LENGTH_KEYWORD_ARGUMENT
)
VarArgTypingIterable = VariableLengthArgumentTypingIterable
KwArgTypingIterable = VariableLengthKeywordArgumentTypingIterable
