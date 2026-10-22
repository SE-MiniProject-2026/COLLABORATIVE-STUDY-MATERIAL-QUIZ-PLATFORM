import io

from nicegui import ui

from auth import authenticate_user, register_student
from database import init_db, get_db
from services import (
    create_test,
    delete_material,
    delete_test,
    get_material_path,
    get_performance_summary,
    get_test_results,
    get_tests,
    search_materials,
    submit_quiz_attempt,
    upload_material,
)

init_db()
current_user = {"user": None}


def refresh_page():
    ui.navigate.to("/")


@ui.page("/")
def main_page():
    ui.label("Collaborative Study Material & Quiz Platform").classes(
        "text-2xl font-bold mb-4"
    )

    if not current_user["user"]:
        with ui.card().classes("w-96 mx-auto p-6"):
            ui.label("Login to CSMQ").classes("text-xl mb-2")
            username = ui.input("Username")
            password = ui.input("Password", password=True)

            def login():
                user = authenticate_user(username.value, password.value)
                if user:
                    current_user["user"] = user
                    refresh_page()
                else:
                    ui.notify("Invalid credentials or deactivated account.", type="negative")

            ui.button("Login", on_click=login).classes("w-full")

            ui.separator()
            ui.label("New students can register below.")
            register_username = ui.input("New username")
            register_password = ui.input("New password", password=True)

            def register():
                if register_student(register_username.value, register_password.value):
                    ui.notify("Registration successful. You are now logged in.", type="positive")
                    current_user["user"] = authenticate_user(
                        register_username.value, register_password.value
                    )
                    refresh_page()
                else:
                    ui.notify("Username may already exist or fields are empty.", type="negative")

            ui.button("Register as Student", on_click=register).classes("w-full")
            
    return

    user = current_user["user"]
    ui.label(f"Welcome, {user['username']} ({user['role']})").classes("text-lg")
    ui.button(
        "Logout",
        on_click=lambda: (current_user.update({"user": None}), refresh_page()),
    ).classes("bg-red-500 text-white")

    with ui.tabs().classes("w-full mt-4") as tabs:
        materials_tab = ui.tab("Shared Materials")
        tests_tab = ui.tab("Tests")
        if user["role"] == "Admin":
            admin_tab = ui.tab("Admin Management")
            admin_results_tab = ui.tab("Test Results")
        if user["role"] == "Student":
            scores_tab = ui.tab("My Results")

    with ui.tab_panels(tabs, value=materials_tab).classes("w-full"):
        with ui.tab_panel(materials_tab):
            ui.label("All users share this material library.").classes("font-bold")
            search = ui.input("Search by title, subject, or description")
            material_list = ui.column()

            def render_materials():
                material_list.clear()
                with material_list:
                    for material in search_materials(search.value or ""):
                        with ui.row().classes("items-center"):
                            ui.label(
                                f"{material['title']} [{material['subject']}] - "
                                f"{material['description'] or ''}"
                            )
                            path = get_material_path(material["id"])
                            if path:
                                ui.button(
                                    "Download",
                                    on_click=lambda path=path: ui.download(path),
                                )
                            if user["role"] == "Admin":
                                ui.button(
                                    "Delete",
                                    on_click=lambda material_id=material["id"]: (
                                        delete_material(material_id),
                                        render_materials(),
                                    ),
                                ).props("color=negative")

            search.on("update:model-value", render_materials)
            render_materials()

            ui.label("Add a file to the shared library").classes("font-bold mt-4")
            title = ui.input("Title")
            subject = ui.input("Subject")
            description = ui.input("Description")

            async def handle_upload(event):
                try:
                    file_data = await event.file.read()
                    upload_material(
                        title.value,
                        subject.value,
                        description.value,
                        io.BytesIO(file_data),
                        user["id"],
                        event.file.name,
                    )
                    ui.notify("File uploaded.", type="positive")
                    render_materials()
                except (OSError, ValueError) as error:
                    ui.notify(str(error), type="negative")

            ui.upload(on_upload=handle_upload, auto_upload=True)
