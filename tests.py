import unittest
from database import init_db, get_db
from auth import create_user, authenticate_user
from services import create_question, create_quiz, submit_quiz_attempt

class CSMQTestCase(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_auth_and_rbac(self):
        create_user("student1", "securepass123", "Student")
        user = authenticate_user("student1", "securepass123")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "Student")

    def test_quiz_evaluation(self):
        create_user("contrib1", "pass", "Contributor")
        conn = get_db()
        c_id = conn.execute("SELECT id FROM users WHERE username = 'contrib1'").fetchone()["id"]
        conn.close()
        
        create_question("What is 2+2?", "2,3,4,5", "4", "Math", c_id)
        conn = get_db()
        q_id = conn.execute("SELECT id FROM questions WHERE topic = 'Math'").fetchone()["id"]
        conn.close()
        
        create_quiz("Math Quiz 1", "Basic math", [q_id], c_id)
        conn = get_db()
        quiz_id = conn.execute("SELECT id FROM quizzes WHERE title = 'Math Quiz 1'").fetchone()["id"]
        s_id = conn.execute("SELECT id FROM users WHERE role = 'Student'").fetchone()
        if not s_id:
            create_user("student2", "pass", "Student")
            s_id = conn.execute("SELECT id FROM users WHERE username = 'student2'").fetchone()["id"]
        else:
            s_id = s_id["id"]
        conn.close()
        
        # Test correct answer evaluation
        score = submit_quiz_attempt(s_id, quiz_id, {str(q_id): "4"})
        self.assertEqual(score, 100.0)

if __name__ == "__main__":
    unittest.main()
