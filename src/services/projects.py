from src.core.base import BaseService
from src.models import projects


class ProjectsService(BaseService):
    collection_name = "projects"
    serializer = projects.Project
