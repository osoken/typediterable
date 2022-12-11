from collections.abc import Iterable
from typing import Any, Generic, Type, TypeVar

T = TypeVar("T")


class GenericTypingIterable(Generic[T]):
    def __init__(self, t: Type[T]):
        self._t = t

    def __call__(self, iter: Iterable[Any]) -> Iterable[T]:
        for d in iter:
            yield self._t(d)  # type: ignore [call-arg]


class GenericTypingIterableFactory:
    def __getitem__(self, t: Type[T]) -> GenericTypingIterable[T]:
        return GenericTypingIterable[T](t)


TypingIterable = GenericTypingIterableFactory()
