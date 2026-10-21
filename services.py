import os
import json
from database import get_db, UPLOAD_DIR, TEST_DIR

def upload_material(title, subject, description, file_obj, uploader_id, filename=None):
    filename = os.path.basename(filename or file_obj.name)
    if not title.strip() or not subject.strip():
        raise ValueError("Title and subject are required")
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(file_obj.read())
        
    conn = get_db()
    conn.execute("INSERT INTO materials (title, subject, description, filename, uploader_id) VALUES (?, ?, ?, ?, ?)",
                 (title, subject, description, filename, uploader_id))
    conn.commit()
    conn.close()
    return True


def delete_material(material_id):
    conn = get_db()
    material = conn.execute(
        "SELECT filename FROM materials WHERE id = ?", (material_id,)
    ).fetchone()
    if not material:
        conn.close()
        return False
    filepath = os.path.join(UPLOAD_DIR, material["filename"])
    if os.path.exists(filepath):
        os.remove(filepath)
    conn.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()
    return True

def get_material_path(material_id):
    conn = get_db()
    material = conn.execute(
        "SELECT filename FROM materials WHERE id = ?", (material_id,)
    ).fetchone()
    conn.close()
    if not material:
        return None
    filepath = os.path.join(UPLOAD_DIR, material["filename"])
    return filepath if os.path.isfile(filepath) else None

def search_materials(query=""):
    conn = get_db()
    q = f"%{query}%"
    rows = conn.execute("SELECT * FROM materials WHERE title LIKE ? OR subject LIKE ? OR description LIKE ?", (q, q, q)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_question(text, options, correct_answer, topic, creator_id):
    conn = get_db()
    conn.execute("INSERT INTO questions (question_text, options, correct_answer, topic, creator_id) VALUES (?, ?, ?, ?, ?)",
                 (text, options, correct_answer, topic, creator_id))
    conn.commit()
    conn.close()

def create_quiz(title, instructions, question_ids, creator_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quizzes (title, instructions, creator_id) VALUES (?, ?, ?)", (title, instructions, creator_id))
    quiz_id = cursor.lastrowid
    for q_id in question_ids:
        cursor.execute("INSERT INTO quiz_questions (quiz_id, question_id) VALUES (?, ?)", (quiz_id, q_id))
    conn.commit()
    conn.close()

def create_test(title, instructions, questions, creator_id):
    title = (title or "").strip()
    instructions = (instructions or "").strip()
    if not title or not isinstance(questions, list) or not questions:
        raise ValueError("A test requires a title and at least one question")
    for question in questions:
        if (
            not isinstance(question, dict)
            or not question.get("question")
            or not isinstance(question.get("options"), list)
            or len(question["options"]) < 2
            or question.get("answer") not in question["options"]
        ):
            raise ValueError("Each question needs text, options, and a valid answer")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO quizzes (title, instructions, is_published, creator_id) VALUES (?, ?, 1, ?)",
        (title, instructions, creator_id),
    )
    test_id = cursor.lastrowid
    with open(os.path.join(TEST_DIR, f"{test_id}.json"), "w", encoding="utf-8") as file:
        json.dump(
            {"id": test_id, "title": title, "instructions": instructions,
             "questions": questions},
            file,
            indent=2,
        )
    conn.commit()
    conn.close()
    return test_id

def get_tests():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, instructions FROM quizzes WHERE is_published = 1 ORDER BY id DESC"
    ).fetchall()
    conn.close()
    tests = []
    for row in rows:
        path = os.path.join(TEST_DIR, f"{row['id']}.json")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as file:
                tests.append(json.load(file))
    return tests

def delete_test(test_id):
    conn = get_db()
    conn.execute("DELETE FROM quiz_questions WHERE quiz_id = ?", (test_id,))
    conn.execute("DELETE FROM quizzes WHERE id = ?", (test_id,))
    conn.commit()
    conn.close()
    path = os.path.join(TEST_DIR, f"{test_id}.json")
    if os.path.isfile(path):
        os.remove(path)

def get_test_results(test_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT attempts.score, attempts.submission_time, users.username
           FROM attempts JOIN users ON users.id = attempts.student_id
           WHERE attempts.quiz_id = ? ORDER BY attempts.submission_time DESC""",
        (test_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
