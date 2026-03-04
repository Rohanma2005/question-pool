
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

with engine.connect() as connection:
    trans = connection.begin()
    try:
        print("Adding 'question_type' column...")
        connection.execute(text("ALTER TABLE tbl_questions ADD COLUMN question_type VARCHAR(32) NOT NULL DEFAULT 'descriptive'"))
        
        print("Adding 'options' column...")
        connection.execute(text("ALTER TABLE tbl_questions ADD COLUMN options JSON NULL"))
        
        trans.commit()
        print("Migration successful!")
    except Exception as e:
        trans.rollback()
        print(f"Migration failed: {e}")
