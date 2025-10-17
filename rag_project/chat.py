import reflex as rx


def chat_input_area() -> rx.Component:
    """The chat input area with visual-only buttons for UI demonstration."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.input(
                    placeholder="Type something...",
                    class_name="w-full bg-transparent outline-none border-none text-white placeholder:text-white/30 px-4 py-2",
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("paperclip", class_name="h-4 w-4"),
                    "Attach",
                    type="button",
                    on_click=rx.toast("This is a UI demonstration", duration=3000),
                    class_name="flex items-center gap-2 text-white px-4 py-2 rounded-full border border-white/20 bg-transparent hover:bg-[#E77AFF21] transition-colors",
                ),
                rx.el.button(
                    rx.icon("arrow-up", class_name="h-4 w-4"),
                    type="button",
                    on_click=rx.toast("This is a UI demonstration", duration=3000),
                    class_name="w-8 h-8 rounded-[14px] bg-[#6F3F7A] text-black flex items-center justify-center hover:bg-[#D377E8] transition-colors",
                ),
                class_name="flex items-center justify-between w-full mt-2",
            ),
            class_name="w-full",
        ),
        class_name="fixed bottom-2.5 w-[95%] max-w-2xl mx-auto p-4 rounded-[38px] bg-[#272137F8] border border-white/10 flex flex-col gap-2",
    )