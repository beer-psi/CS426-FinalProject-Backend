from dataclasses import dataclass
from typing import Annotated

from litestar.datastructures import UploadFile
from litestar.params import Parameter


@dataclass
class CreateQuizFromFile:
    file: UploadFile
    prompt: str | None = None
    question_count: Annotated[int, Parameter(gt=0, le=50)] = 20
