from abc import ABC, abstractmethod

from .models import TaskList


class TaskListsRepository(ABC):
    @abstractmethod
    async def insert(self, user_id: int, name: str) -> TaskList: ...
