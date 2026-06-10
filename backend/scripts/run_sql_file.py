from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import get_connection


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/run_sql_file.py <sql-file>")

    sql_path = Path(sys.argv[1]).resolve()
    sql_text = sql_path.read_text(encoding="utf-8")
    statements = [statement.strip() for statement in sql_text.split(";") if statement.strip()]

    with get_connection() as connection:
        try:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    print(f"Executed {len(statements)} statements from {sql_path}")


if __name__ == "__main__":
    main()
