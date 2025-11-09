import reflex as rx
from rag_project.state import RAGState, UploadedFile


def uploaded_file_card(file_info: UploadedFile) -> rx.Component:
    """A card to display an uploaded file with an optional remove button."""
    return rx.el.div(
        rx.icon("file-text", class_name="h-4 w-4 text-gray-400"),
        rx.el.span(
            file_info["filename"],
            class_name="text-sm font-medium text-gray-400 truncate",
        ),
        rx.cond(
            RAGState.is_processing,
            rx.el.div(),
            rx.el.button(
                rx.icon("x", class_name="h-3 w-3 text-gray-400"),
                on_click=lambda: RAGState.remove_file(file_info["file_id"]),
                class_name="p-1 rounded-full hover:bg-[#d5c0d85f] transition-colors",
                type="button",
            ),
        ),
        class_name="flex items-center gap-2 bg-transparent border border-[#c1a2c688] rounded-[15px] px-3 py-2 w-fit max-w-full",
    )