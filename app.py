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