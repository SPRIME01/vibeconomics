# Type stubs for dspy to resolve Pylance errors
from typing import Any
class Signature:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class InputField:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class OutputField:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class predict:
    def __init__(self, signature: Any, *args: Any, **kwargs: Any) -> None: ...
    def __call__(self, input: str) -> Any: ...

class dsp:
    class LM:
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...

def context(lm: Any) -> Any: ...
