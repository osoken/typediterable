import sys

if sys.version_info < (3, 9):
    from typing import Callable, Iterable
else:
    from collections.abc import Callable, Iterable

from enum import Enum
from typing import Any, Generic, Optional, Type, TypeVar

T = TypeVar("T")


class ArgumentType(str, Enum):
    one_argument = "one_argument"
    variable_length_argument = "variable_length_argument"
    variable_length_keyword_argument = "variable_length_keyword_argument"


class GenericTypingIterable(Generic[T]):
    def __init__(self, t: Type[T]):
        self._t = t

    def _cast(self, d: Any) -> T:
        return self._t(d)  # type: ignore [call-arg]

    def __call__(
        self, iter: Iterable[Any], on_error: Optional[Callable[[Any, int, Exception], None]] = None
    ) -> Iterable[T]:
        if on_error is not None:
            for i, d in enumerate(iter):
                try:
                    yield self._cast(d)
                except Exception as e:
                    on_error(d, i, e)
        else:
            for d in iter:
                yield self._cast(d)


class GenericVariableLengthArgumentTypingIterable(Generic[T], GenericTypingIterable[T]):
    def _cast(self, d: Any) -> T:
        return self._t(*d)


class GenericVariableLengthArgumentKeywordTypingIterable(Generic[T], GenericTypingIterable[T]):
    def _cast(self, d: Any) -> T:
        return self._t(**d)


class GenericTypingIterableFactory:
    def __init__(self, argument_type: ArgumentType = ArgumentType.one_argument):
        self._argument_type = argument_type

    def __getitem__(self, t: Type[T]) -> GenericTypingIterable[T]:
        if self._argument_type == ArgumentType.variable_length_argument:
            return GenericVariableLengthArgumentTypingIterable[T](t)
        if self._argument_type == ArgumentType.variable_length_keyword_argument:
            return GenericVariableLengthArgumentKeywordTypingIterable[T](t)
        return GenericTypingIterable[T](t)


TypingIterable = GenericTypingIterableFactory()
VariableLengthArgumentTypingIterable = GenericTypingIterableFactory(argument_type=ArgumentType.variable_length_argument)
VariableLengthKeywordArgumentTypingIterable = GenericTypingIterableFactory(
    argument_type=ArgumentType.variable_length_keyword_argument
)
