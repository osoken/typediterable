# typingiterable

`typingiterable` is a simple python package for the actual typing of each element of an iterable with type hint notation.

## Install

```
pip install git+ssh://git@github.com/osoken/typingiterable.git
```

## Features and Examples

### Actual Typing with Type Hint Notation

The following example shows how the main component `typingiterable.TypingIterable` works:

```py
from dataclasses import dataclass
from typingiterable import TypingIterable

@dataclass
class User:
    id: int
    name: str

raw_data = [{"id": 0, "name": "Alice"}, {"id": 1, "name": "Bob"}]
for d in TypingIterable[User](raw_data):
    assert isinstance(d, User)
```

It is equivalent to write:

```py
from dataclasses import dataclass
from typingiterable import TypingIterable

@dataclass
class User:
    id: int
    name: str

raw_data = [{"id": 0, "name": "Alice"}, {"id": 1, "name": "Bob"}]
for d in (User(**d) for d in raw_data):
    assert isinstance(d, User)
```

### Error Handling

`typingiterable.TypingIterable` also has the error handling feature.

```py
from dataclasses import dataclass
from typingiterable import TypingIterable
from collections.abc import Mapping
from typing import Union

@dataclass
class User:
    id: int
    name: str

def error_handler(d: Mapping[int, Union[int, str]], i: int, e: Exception) -> None:
    print(f"{i}th element `{d}` is invalid due to the following error: {e}")

raw_data = [{"id": 0, "name": "Alice"}, {"name": "lack of id"}, {"id": 1, "name": "Bob"}]
for d in TypingIterable[User](raw_data, on_error=error_handler):
    assert isinstance(d, User)
```

The above example prints the following string:

```
1th element `{'name': 'lack of id'}` is invalid due to the following error: User.__init__() missing 1 required positional argument: 'id'
```

and it doesn't stop iterating.
The example is equivalent to write:

```py
from dataclasses import dataclass
from typingiterable import TypingIterable
from collections.abc import Mapping
from typing import Union

@dataclass
class User:
    id: int
    name: str

raw_data = [{"id": 0, "name": "Alice"}, {"name": "lack of id"}, {"id": 1, "name": "Bob"}]
for i, raw_d in enumerate(raw_data):
    try:
        d = User(**raw_d)
    except Exception as e:
        print(f"{i}th element `{raw_d}` is invalid due to the following error: {e}")
    assert isinstance(d, User)
```

### Automatic Unpacking Arguments

`typingiterable.TypingIterable` checks the signature and automatically unpack the argument. If the type's constructor is single-argument, it doesn't unpack.

```py
from typingiterable import TypingIterable

raw_data = ["1", "2", "3", "4"]
for d in TypingIterable[int](raw_data):
    assert isinstance(d, int)
```
