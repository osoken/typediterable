from collections.abc import Callable, Iterable
from typing import Any, Generic, Optional, Type, TypeVar

T = TypeVar("T")


class GenericTypingIterable(Generic[T]):
    def __init__(self, t: Type[T]):
        self._t = t

    def __call__(
        self, iter: Iterable[Any], on_error: Optional[Callable[[Any, int, Exception], None]] = None
    ) -> Iterable[T]:
        if on_error is not None:
            for i, d in enumerate(iter):
                try:
                    yield self._t(d)  # type: ignore [call-arg]
                except Exception as e:
                    on_error(d, i, e)
        else:
            for d in iter:
                yield self._t(d)  # type: ignore [call-arg]


class GenericTypingIterableFactory:
    def __getitem__(self, t: Type[T]) -> GenericTypingIterable[T]:
        return GenericTypingIterable[T](t)


TypingIterable = GenericTypingIterableFactory()
