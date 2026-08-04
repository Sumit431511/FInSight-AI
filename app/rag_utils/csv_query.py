import re
import os
import sqlite3
import tabulate
from pathlib import Path

from dotenv import load_dotenv

try:
    import duckdb
except ImportError:
    duckdb = None

try:
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
except ImportError:
    ChatGroq = None
    ChatPromptTemplate = None
    StrOutputParser = None

from app.config import get_data_dir

load_dotenv()

DB_PATH = str(get_data_dir("roles_docs.db"))
DUCKDB_FILE = str(get_data_dir("static", "data", "structured_queries.duckdb"))


def _create_duckdb_connection():
    if duckdb is None:
        return None

    try:
        conn = duckdb.connect(DUCKDB_FILE, read_only=False)
    except Exception as exc:
        print(f"DuckDB file connection failed, using in-memory fallback: {exc}")
        conn = duckdb.connect(":memory:")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tables_metadata (
            table_name TEXT,
            role TEXT
        )
        """
    )
    return conn


duck_conn = _create_duckdb_connection()

llm = None
if ChatGroq is not None:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )

def get_allowed_tables_for_role(role: str) -> list[str]:
    if duck_conn is None:
        return []

    if role.lower() == "c-level":
        query = "SELECT table_name FROM tables_metadata"
        return [row[0] for row in duck_conn.execute(query).fetchall()]
    elif role.lower() == "general":
        query = "SELECT table_name FROM tables_metadata WHERE role = 'general'"
        return [row[0] for row in duck_conn.execute(query).fetchall()]
    else:
        query = """
        SELECT table_name FROM tables_metadata
        WHERE role = ? OR role = 'general'
        """
        return [row[0] for row in duck_conn.execute(query, [role]).fetchall()]

def extract_tables_from_sql(sql: str) -> list[str]:
    # Extract tables used in FROM and JOIN clauses
    return re.findall(r'FROM\s+(\w+)|JOIN\s+(\w+)', sql, flags=re.IGNORECASE)

def flatten_matches(matches: list[tuple]) -> list[str]:
    return [item for tup in matches for item in tup if item]

FORBIDDEN = ["insert", "update", "delete", "drop", "alter", "create"]

def is_safe_query(sql: str) -> bool:
    lowered = sql.strip().lower().rstrip(";")
    return lowered.startswith("select") and all(word not in lowered for word in FORBIDDEN)

def translate_nl_to_sql(question: str, allowed_tables: list[str]) -> str:
    print("translate_nl_to_sql() called")
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    print("Using DB path:", DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT filename, headers_str FROM documents 
        WHERE embedded = 1 AND headers_str IS NOT NULL
    """)
    rows = cur.fetchall()
    print("Raw rows from DB:", rows)
    conn.close()

    schemas = []
    for filename, headers_str in rows:
        try:
            print("inside schemas")
            table_name = Path(filename).stem.replace("-", "_")
            print(table_name)
            cols = ", ".join(headers_str.split(","))
            print(cols)
            schemas.append(f"Table: {table_name}\nColumns: {cols}")
        except Exception as e:
            print(f"❌ Error while building schema for {filename}: {e}")


    print("Schemas:", schemas)

    schema_block = "\n\n".join(schemas)
    print("schema_block:\n", schema_block)

    sql_prompt = ChatPromptTemplate.from_template(
        """
        You are an assistant that converts natural language questions into SQL.

        Use ONLY these schemas:

        {schema}

        Rules:

        - Generate ONLY SELECT statements.
        - Never generate INSERT, UPDATE, DELETE, DROP, ALTER.
        - Use only the tables listed.
        - Use exact column names.
        - Return ONLY SQL.
        - No markdown.
        - No explanation.

        Question:

        {question}

        SQL:
        """
        )

    try:
        chain = (
            sql_prompt
            | llm
            | StrOutputParser()
        )

        response_text = chain.invoke({
            "schema": schema_block,
            "question": question
        })

        print("Raw SQL:\n", response_text)
        response_text = (
            response_text
            .replace("```sql", "")
            .replace("```", "")
            .strip()
            )

        return response_text

    except Exception as e:
        print("❌ LLM call failed:", e)
        return "Error generating SQL"

async def ask_csv(question: str, role: str, username: str, return_sql: bool = False) -> dict:
    if duck_conn is None:
        return {"answer": "❌ SQL engine is unavailable in this deployment environment.", "error": True}

    allowed_tables = get_allowed_tables_for_role(role)

    try:
        sql = translate_nl_to_sql(question, allowed_tables)
        print(f"[SQL GENERATED]:\n{sql}")

        if not is_safe_query(sql):
            return {"answer": "Only SELECT queries are allowed.", "error": True}

        raw_matches = extract_tables_from_sql(sql)
        referenced_tables = flatten_matches(raw_matches)

        for table in referenced_tables:
            if table not in allowed_tables:
                return {"answer": f"Access denied to table: {table}", "error": True}

        result = duck_conn.execute(sql).fetchall()
        columns = [desc[0] for desc in duck_conn.description]
        output = [list(row) for row in result]

        markdown_table = tabulate.tabulate(output, headers=columns, tablefmt="github")
        response = {
            "answer": markdown_table if output else "Query executed, but no results found."
        }

        if return_sql:
            response["sql"] = sql

        return response

    except Exception as e:
        return {"answer": f"❌ Error: {str(e)}", "error": True}
