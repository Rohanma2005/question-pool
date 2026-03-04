
import os
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def debug_generation():
    engine = create_engine(os.getenv('DATABASE_URL'))
    course_id = 3 # Fundamentals of Programming
    
    with open("debug_report.txt", "w") as f:
        with engine.connect() as conn:
            # Get Template
            res = conn.execute(text("SELECT categories FROM tbl_templates WHERE course_id=:cid"), {"cid": course_id}).fetchone()
            if not res:
                f.write("No template found for course 3\n")
                return
            
            categories = json.loads(res[0])
            f.write("Template Categories:\n")
            for cat in categories:
                f.write(f"  Section {cat['section']}: Type={cat['question_type']}, Marks={cat['mark_per_question']}, Required={cat['number_of_questions']}\n")
                
            # Get Topics
            topics = conn.execute(text("SELECT id, title FROM tbl_topics WHERE course_id=:cid"), {"cid": course_id}).fetchall()
            f.write("\nTopics:\n")
            for t in topics:
                f.write(f"  ID {t[0]}: {t[1]}\n")
                
            # Get Questions Summary
            questions = conn.execute(text("SELECT id, topic_id, difficulty, mark_value, question_type, active FROM tbl_questions WHERE course_id=:cid"), {"cid": course_id}).fetchall()
            f.write("\nQuestions in Pool:\n")
            for q in questions:
                f.write(f"  ID {q[0]}: Topic={q[1]}, Diff={q[2]}, Marks={q[3]}, Type={q[4]}, Active={q[5]}\n")

if __name__ == "__main__":
    debug_generation()
