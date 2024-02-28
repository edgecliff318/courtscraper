from src.core.base import BaseService
from src.models import tasks


class TasksService(BaseService):
    collection_name = "tasks"
    serializer = tasks.Task
