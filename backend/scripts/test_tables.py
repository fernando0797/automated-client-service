from sqlalchemy import text

from src.persistence.database import create_db_session


def main() -> None:
    db = create_db_session()

    try:
        result = db.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
                """
            )
        )

        tables = [row[0] for row in result.fetchall()]

        print("Tables found:")
        for table in tables:
            print(f"- {table}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
