from admin.views.base import BaseAdminView
from core.config import MEDIA_ROOT
from starlette.requests import Request
from starlette_admin import BooleanField, HasOne, IntegerField, StringField, TextAreaField


class BookAdminView(BaseAdminView):
    name = "Kitob"
    name_plural = "Kitoblar"
    icon = "fa fa-book-open"

    fields = [
        "id",
        StringField("title", label="Sarlavha", required=True),
        StringField("author", label="Muallif"),
        StringField("category", label="Turi"),
        HasOne("topic", label="Mavzu", identity="mavzu"),
        TextAreaField("description", label="Tavsif"),
        StringField("file_name", label="Fayl nomi", read_only=True),
        IntegerField("file_size", label="Hajmi (bayt)", read_only=True),
        IntegerField("downloads", label="Yuklab olishlar", read_only=True),
        IntegerField("order", label="Tartib"),
        BooleanField("is_active", label="Faol"),
    ]
    # File itself is uploaded via the "Kitob yuklash" tool page
    exclude_fields_from_create = BaseAdminView.exclude_fields_from_create + [
        "file_path", "file_name", "file_size", "downloads",
    ]
    exclude_fields_from_list = BaseAdminView.exclude_fields_from_list + ["file_path", "description"]

    column_list = ["id", "title", "category", "topic", "file_name", "downloads", "is_active"]
    column_searchable_list = ["title", "author", "category"]
    column_sortable_list = ["is_active", "downloads", "createdAt"]

    async def delete(self, request: Request, pks: list) -> int | None:
        # Remove files from disk alongside the DB rows
        for pk in pks:
            obj = await self.find_by_pk(request, pk)
            if obj and obj.file_path:
                try:
                    (MEDIA_ROOT / obj.file_path).unlink(missing_ok=True)
                except OSError:
                    pass
        return await super().delete(request, pks)
