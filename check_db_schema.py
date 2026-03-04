
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

with engine.connect() as connection:
    result = connection.execute(text("DESCRIBE tbl_questions"))
    with open("schema_info.txt", "w") as f:
        f.write("Columns in 'tbl_questions':\n")
        for row in result:
            f.write(f"COL: {row[0]} | TYPE: {row[1]}\n")
    print("Schema info written to schema_info.txt")
