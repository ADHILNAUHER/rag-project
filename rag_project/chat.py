import reflex as rx
from rag_project.style import input_box, upload_button, send_buttom, action_bar


def chat_input_area() -> rx.Component:
    """The chat input area with visual-only buttons for UI demonstration."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.input(
                    placeholder="Type something...",
                    class_name=input_box,
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("paperclip", class_name="h-4 w-4"),
                    "Attach",
                    type="button",
                    on_click=rx.toast("This is a UI demonstration",  duration=3000),
                    class_name=upload_button,
                ),
                rx.el.button(
                    rx.icon("arrow-up", class_name="h-4 w-4"),
                    type="button",
                    on_click=rx.toast("This is a UI demonstration", duration=3000),
                    class_name=send_buttom,
                ),
                class_name="flex items-center justify-between w-full mt-2",
            ),
            class_name="w-full",
        ),
        class_name=action_bar,
    )
