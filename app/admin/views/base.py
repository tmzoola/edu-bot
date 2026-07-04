from core.config import settings
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class BaseAdminView(ModelView):
    exclude_fields_from_create = ["createdAt", "updatedAt"]
    exclude_fields_from_edit = ["createdAt", "updatedAt"]
    exclude_fields_from_list = ["createdAt", "updatedAt"]

    def can_delete(self, request: Request) -> bool:
        if settings.APP_MODE == "PRODUCTION":
            return False
        return True
