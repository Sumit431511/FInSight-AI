import os
import tabulate

from dotenv import load_dotenv

try:
    import duckdb
except ImportError:
    duckdb = None

try:
    import sqlglot
    from sqlglot import exp
except ImportError:
    sqlglot = None
    exp = None

try:
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
except ImportError:
    ChatGroq = None
    ChatPromptTemplate = None
    StrOutputParser = None

from app.db import get_duckdb, get_sqlite_conn
from app.config import get_groq_model

load_dotenv()


def get_duck_conn():
    if duckdb is None:
        return None
    return get_duckdb()


llm = None
if ChatGroq is not None:
    llm = ChatGroq(
        model=get_groq_model(),
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )


def get_allowed_tables_for_role(role: str) -> list[str]:
    duck_conn = get_duck_conn()
    if duck_conn is None:
        return []

    if role.lower() == "c-level":
        query = "SELECT table_name FROM tables_metadata"
        return [row[0] for row in duck_conn.execute(query).fetchall()]
    elif role.lower() == "general":
        query = "SELECT table_name FROM tables_metadata WHERE lower(role) = 'general'"
        return [row[0] for row in duck_conn.execute(query).fetchall()]
    else:
        query = """
        SELECT table_name FROM tables_metadata
        WHERE lower(role) = ? OR lower(role) = 'general'
        """
        return [row[0] for row in duck_conn.execute(query, [role.lower()]).fetchall()]

def extract_tables_from_sql(sql: str) -> list[str]:
    """Return physical tables from one validated DuckDB SELECT statement."""
    if sqlglot is None or exp is None:
        return []
    try:
        statement = sqlglot.parse(sql, read="duckdb")[0]
        return [table.name for table in statement.find_all(exp.Table)]
    except Exception:
        return []

def is_safe_query(sql: str) -> bool:
    """Allow exactly one plain read-only SELECT query, or fail closed."""
    if sqlglot is None or exp is None:
        return False
    if not sql or ";" in sql or "--" in sql or "/*" in sql:
        return False
    try:
        statements = sqlglot.parse(sql, read="duckdb")
        if len(statements) != 1 or not isinstance(statements[0], exp.Select):
            return False
        return not any(
            statements[0].find(node_type) is not None
            for node_type in (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create)
        )
    except Exception:
        return False

def translate_nl_to_sql(question: str, allowed_tables: list[str]) -> str:
    print("translate_nl_to_sql() called")
    if not allowed_tables:
        return ""

    placeholders = ", ".join("?" for _ in allowed_tables)
    with get_sqlite_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT table_name, headers_str FROM documents
            WHERE embedded = 1 AND headers_str IS NOT NULL
              AND table_name IN ({placeholders})
            """,
            allowed_tables,
        ).fetchall()

    schemas = []
    for table_name, headers_str in rows:
        try:
            cols = ", ".join(headers_str.split(","))
            schemas.append(f"Table: {table_name}\nColumns: {cols}")
        except Exception:
            continue

    schema_block = "\n\n".join(schemas)

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

        response_text = (
            response_text
            .replace("```sql", "")
            .replace("```", "")
            .strip()
            )

        return response_text

    except Exception:
        return "Error generating SQL"

async def ask_csv(question: str, role: str, username: str, return_sql: bool = False) -> dict:
    duck_conn = get_duck_conn()
    if duck_conn is None:
        return {"answer": "❌ SQL engine is unavailable in this deployment environment.", "error": True}

    allowed_tables = get_allowed_tables_for_role(role)
    if not allowed_tables:
        return {"answer": "No structured data is available for your role.", "error": True}

    try:
        sql = translate_nl_to_sql(question, allowed_tables)
        if not is_safe_query(sql):
            return {"answer": "The generated query was not a permitted read-only SELECT statement.", "error": True}

        referenced_tables = extract_tables_from_sql(sql)

        for table in set(referenced_tables):
            if table not in allowed_tables:
                return {"answer": "The query requested data outside your access scope.", "error": True}

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
