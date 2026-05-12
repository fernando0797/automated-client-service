from src.core.memory_models import ConversationMemory
from src.persistence.database import create_db_session
from src.persistence.repositories.conversation_memory_repository import (
    SQLConversationMemoryStore,
)


def main() -> None:
    db = create_db_session()

    try:
        store = SQLConversationMemoryStore(db)

        memory = ConversationMemory(
            memory="The user reported that the phone overheats after charging."
        )

        store.save(ticket_id="ticket_test_001", memory=memory)

        loaded = store.load("ticket_test_001")

        print("Loaded memory:")
        print(loaded)

    finally:
        db.close()


if __name__ == "__main__":
    main()
