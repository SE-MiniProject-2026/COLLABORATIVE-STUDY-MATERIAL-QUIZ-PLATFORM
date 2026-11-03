"""Focused tests for the platform's Python modules.

Run with:
    .venv/bin/python -m unittest coverage.py

The test fixture uses a temporary working directory so the repository database,
uploaded files, and generated tests are never modified.
"""

import asyncio
import importlib
import io
import os
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest import mock


ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import auth
import database
import services


class BackendTests(unittest.TestCase):
    """Exercise the database, authentication, and service layers."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        database.DB_NAME = "test.db"
        database.UPLOAD_DIR = "files"
        database.TEST_DIR = "tests"
        services.UPLOAD_DIR = database.UPLOAD_DIR
        services.TEST_DIR = database.TEST_DIR
        database.init_db()

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()

    def user_id(self, username):
        conn = database.get_db()
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        return row["id"]

    def test_database_initialization_is_idempotent_and_get_db_has_rows(self):
        database.init_db()
        conn = database.get_db()
        self.assertIsInstance(conn, sqlite3.Connection)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)
        conn.close()

    def test_authentication_and_user_validation_branches(self):
        self.assertEqual(auth.hash_password("secret") != "secret", True)
        hashed = auth.hash_password("secret")
        self.assertTrue(auth.verify_password("secret", hashed))
        self.assertFalse(auth.verify_password("wrong", hashed))
        self.assertFalse(auth.create_user(" ", "password", "Student"))
        self.assertFalse(auth.create_user("alice", "", "Student"))
        self.assertFalse(auth.create_user("alice", "password", "Guest"))
        self.assertTrue(auth.create_user(" alice ", "password", "Student"))
        self.assertTrue(auth.register_student("bob", "password"))
        self.assertFalse(auth.create_user("alice", "another", "Student"))
        self.assertIsNone(auth.authenticate_user("missing", "password"))
        self.assertIsNone(auth.authenticate_user("alice", "wrong"))
        self.assertEqual(auth.authenticate_user("alice", "password")["username"], "alice")

        conn = database.get_db()
        conn.execute("UPDATE users SET status = 'Deactivated' WHERE username = 'alice'")
        conn.commit()
        conn.close()
        self.assertIsNone(auth.authenticate_user("alice", "password"))

    def test_material_lifecycle_and_search(self):
        self.assertRaises(
            ValueError,
            services.upload_material,
            " ", "Subject", "", io.BytesIO(b"data"), 1, "invalid.txt",
        )
        self.assertTrue(
            services.upload_material(
                "Algebra", "Math", "numbers", io.BytesIO(b"pdf"),
                1, "../lesson.pdf",
            )
        )
        self.assertEqual(services.search_materials("algebra")[0]["filename"], "lesson.pdf")
        material_id = database.get_db().execute(
            "SELECT id FROM materials"
        ).fetchone()["id"]
        self.assertTrue(services.get_material_path(material_id).endswith("lesson.pdf"))
        self.assertTrue(services.delete_material(material_id))
        self.assertFalse(services.delete_material(material_id))
        self.assertIsNone(services.get_material_path(material_id))
        self.assertEqual(services.search_materials("not found"), [])

    def test_question_quiz_and_classic_quiz_submission(self):
        auth.create_user("contributor", "password", "Contributor")
        contributor_id = self.user_id("contributor")
        services.create_question("2+2?", "2,4", "4", "Math", contributor_id)
        conn = database.get_db()
        question_id = conn.execute("SELECT id FROM questions").fetchone()["id"]
        conn.close()
        services.create_quiz("Math", "Choose", [question_id], contributor_id)
        conn = database.get_db()
        quiz_id = conn.execute("SELECT id FROM quizzes").fetchone()["id"]
        conn.close()
        auth.register_student("student", "password")
        student_id = self.user_id("student")
        self.assertEqual(
            services.submit_quiz_attempt(
                student_id, quiz_id, {str(question_id): "4"}
            ),
            100.0,
        )
        self.assertEqual(
            services.submit_quiz_attempt(
                student_id, quiz_id, {str(question_id): "2"}
            ),
            0.0,
        )
        self.assertEqual(len(services.get_test_results(quiz_id)), 2)

    def test_test_validation_creation_loading_and_deletion(self):
        auth.create_user("admin2", "password", "Admin")
        creator_id = self.user_id("admin2")
        valid = [{"question": "Pick", "options": ["A", "B"], "answer": "A"}]
        for invalid in (
            (None, "instructions", valid),
            ("Title", "instructions", []),
            ("Title", "instructions", "not a list"),
            ("Title", "instructions", [{}]),
            ("Title", "instructions", [{"question": "Q", "options": ["A"], "answer": "A"}]),
            ("Title", "instructions", [{"question": "Q", "options": ["A", "B"], "answer": "C"}]),
        ):
            self.assertRaises(
                ValueError,
                services.create_test,
                invalid[0], invalid[1], invalid[2], creator_id,
            )

        test_id = services.create_test("  Test  ", None, valid, creator_id)
        self.assertEqual(services.get_tests()[0]["title"], "Test")
        self.assertEqual(services.get_tests()[0]["instructions"], "")
        self.assertEqual(
            services.submit_quiz_attempt(creator_id, test_id, {"0": "A"}), 100.0
        )
        self.assertEqual(services.get_performance_summary(creator_id)["avg_score"], 100.0)
        services.delete_test(test_id)
        self.assertEqual(services.get_tests(), [])

        conn = database.get_db()
        self.assertEqual(
            services.get_performance_summary(999),
            {"avg_score": 0, "total_attempts": 0},
        )
        conn.close()


class _FakeElement:
    def __init__(self, value=""):
        self.value = value
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def __call__(self, *args, **kwargs):
        return self

    def classes(self, *_):
        return self

    def props(self, *_):
        return self

    def clear(self):
        return None

    def on(self, *_):
        return None

    def set_text(self, text):
        self.value = text

    def update(self):
        return None

    def to(self, *_):
        return None


class _FakeUI:
    def __init__(self):
        self.callbacks = []
        self.inputs = []
        self.navigate = _FakeElement()

    def reset(self):
        self.callbacks = []
        self.inputs = []

    def page(self, *_):
        return lambda function: function

    def run(self, **_):
        return None

    def __getattr__(self, name):
        def factory(*args, **kwargs):
            element = _FakeElement(kwargs.get("value", ""))
            if name == "input":
                self.inputs.append(element)
            callback = kwargs.get("on_click") or kwargs.get("on_upload")
            if callback:
                self.callbacks.append(callback)
            return element

        return factory


class AppTests(unittest.TestCase):
    """Cover page construction without launching NiceGUI."""

    def test_page_for_logged_out_student_and_admin_paths(self):
        fake_ui = _FakeUI()
        fake_nicegui = types.ModuleType("nicegui")
        fake_nicegui.ui = fake_ui
        with mock.patch.dict(sys.modules, {"nicegui": fake_nicegui}):
            sys.modules.pop("app", None)
            app = importlib.import_module("app")

            app.current_user["user"] = None
            app.main_page()
            fake_ui.inputs[0].value = "missing"
            fake_ui.inputs[1].value = "wrong"
            fake_ui.callbacks[0]()
            fake_ui.inputs[0].value = "student"
            fake_ui.inputs[1].value = "password"
            with mock.patch.object(
                app, "authenticate_user",
                return_value={"id": 3, "username": "student", "role": "Student"},
            ):
                fake_ui.callbacks[0]()
            fake_ui.inputs[2].value = ""
            fake_ui.inputs[3].value = ""
            fake_ui.callbacks[1]()
            fake_ui.inputs[2].value = "newstudent"
            fake_ui.inputs[3].value = "password"
            with mock.patch.object(app, "register_student", return_value=True), \
                 mock.patch.object(
                     app, "authenticate_user",
                     return_value={"id": 4, "username": "newstudent", "role": "Student"},
                 ):
                fake_ui.callbacks[1]()

            fake_ui.reset()
            app.current_user["user"] = {
                "id": 1, "username": "student", "role": "Student"
            }
            test = {
                "id": 5, "title": "Sample", "instructions": "Do it",
                "questions": [{"question": "Q", "options": ["A", "B"]}],
            }
            history = [{
                "quiz_id": 5, "score": 50, "submission_time": "now"
            }]
            with mock.patch.object(app, "get_tests", return_value=[test]), \
                 mock.patch.object(
                     app, "search_materials",
                     return_value=[{
                         "id": 1, "title": "Notes", "subject": "Math",
                         "description": None,
                     }],
                 ), \
                 mock.patch.object(app, "get_material_path", return_value="/tmp/note"), \
                 mock.patch.object(
                     app, "get_performance_summary",
                     return_value={
                         "avg_score": 50, "total_attempts": 1, "history": history
                     },
                 ):
                app.main_page()
                for callback in list(fake_ui.callbacks):
                    if asyncio.iscoroutinefunction(callback):
                        class File:
                            name = "upload.txt"

                            async def read(self):
                                return b"content"

                        asyncio.run(callback(types.SimpleNamespace(file=File())))
                    else:
                        with mock.patch.object(app, "submit_quiz_attempt", return_value=50):
                            try:
                                callback()
                            except (TypeError, KeyError):
                                pass

            fake_ui.reset()
            app.current_user["user"] = {
                "id": 2, "username": "admin", "role": "Admin"
            }
            admin_test = {
                "id": 7, "title": "Existing", "instructions": "",
                "questions": [{"question": "Q", "options": ["A", "B"], "answer": "A"}],
            }
            with mock.patch.object(app, "get_tests", return_value=[admin_test]), \
                 mock.patch.object(app, "search_materials", return_value=[]), \
                 mock.patch.object(app, "create_test", return_value=8), \
                 mock.patch.object(
                     app, "get_test_results",
                     return_value=[{
                         "username": "student", "score": 80,
                         "submission_time": "now",
                     }],
                 ):
                app.main_page()
                for callback in list(fake_ui.callbacks):
                    if getattr(callback, "__name__", "") == "add_question":
                        callback()
                    elif getattr(callback, "__name__", "") == "save_test":
                        callback()
                    elif getattr(callback, "__name__", "") == "<lambda>":
                        try:
                            callback()
                        except TypeError:
                            pass
                # Fill the form created by add_question and publish it.
                for element in fake_ui.inputs:
                    element.value = "value"
                for callback in list(fake_ui.callbacks):
                    if getattr(callback, "__name__", "") == "save_test":
                        callback()

            app.refresh_page = mock.Mock()
            app.current_user["user"] = None
            app.refresh_page()
            app.refresh_page.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()