# typingiterable

`typingiterable` is a simple python package for the actual typing of each element of an iterable with type hint notation.

## Install

```
pip install git+ssh://git@github.com/osoken/typingiterable.git
```

## Example

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

