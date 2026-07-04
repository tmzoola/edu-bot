from admin.views.base import BaseAdminView
from models.question import CorrectOption
from starlette_admin import EnumField, HasOne, IntegerField, StringField, TextAreaField


class QuestionAdminView(BaseAdminView):
    name = "Savol"
    name_plural = "Savollar"
    icon = "fa fa-question-circle"

    fields = [
        "id",
        HasOne("quiz", label="Test", identity="test"),
        IntegerField("order", label="Tartib"),
        TextAreaField("text", label="Savol matni", required=True),
        StringField("option_a", label="A variant", required=True),
        StringField("option_b", label="B variant", required=True),
        StringField("option_c", label="C variant", required=True),
        StringField("option_d", label="D variant", required=True),
        EnumField("correct_option", label="To'g'ri javob", enum=CorrectOption, required=True),
        TextAreaField("explanation", label="Izoh (ixtiyoriy)"),
    ]

    column_list = ["id", "quiz", "order", "text", "correct_option"]
    column_searchable_list = ["text"]
    column_sortable_list = ["order"]
    page_size = 50
