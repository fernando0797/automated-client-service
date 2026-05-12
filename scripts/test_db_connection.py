from sqlalchemy import text

from src.persistence.database import create_db_session


def main() -> None:
    db = create_db_session()

    try:
        result = db.execute(text("SELECT version();"))
        version = result.scalar_one()
        print("Connected to PostgreSQL successfully.")
        print(version)
    finally:
        db.close()


if __name__ == "__main__":
    main()
