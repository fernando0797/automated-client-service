from src.core.conversation_state_models import ConversationState
from src.persistence.database import create_db_session
from src.persistence.repositories.conversation_state_repository import (
    SQLConversationStateStore,
)


def main() -> None:
    db = create_db_session()

    try:
        store = SQLConversationStateStore(db)

        state = ConversationState(
            ticket_id="ticket_test_001",
            turn_count=1,
            rag_call_count=1,
            last_turn_id="turn_001",
            status="active",
        )

        store.save(ticket_id=state.ticket_id, state=state)

        loaded = store.get("ticket_test_001")

        print("Loaded state:")
        print(loaded)

    finally:
        db.close()


if __name__ == "__main__":
    main()
