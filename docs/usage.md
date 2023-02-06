# Usage

## `TypedIterable`

### `TypedIterable[T](...)`

Constractor.

#### Type Parameters:

- `T`: The type of each element to be returned.

#### Arguments:

- `it`: `Iterable[Any]`; The iterator of raw values.
- `on_error`: `Callable[[Any, int, Exception], None]]`, optional, default=`None`; Function called when an error occurs on type casting. If the function doesn't raise any exceptions, the iteration continues. The `on_error` should accept three arguments, where `value`, `index` and `exception` mean the value which causes the exception, the index of the value and the exception respectively. If `None`, which is default, raises the exception and stops iteration.
