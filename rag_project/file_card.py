import reflex as rx
from rag_project.state import RAGState, UploadedFile


def uploaded_file_card(file_info: UploadedFile) -> rx.Component:
    """A card to display an uploaded file with a remove button."""
    return rx.el.div(
        rx.icon("file-text", class_name="h-4 w-4 text-gray-500"),
        rx.el.span(
            file_info["filename"],
            class_name="text-sm font-medium text-gray-700 truncate",
        ),
        rx.el.button(
            rx.icon("x", class_name="h-3 w-3 text-gray-500 hover:text-gray-800"),
            on_click=lambda: RAGState.remove_file(file_info["file_id"]),
            class_name="p-1 rounded-full hover:bg-gray-200 transition-colors",
            type="button",
        ),
        class_name="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2 w-fit max-w-full",
    )