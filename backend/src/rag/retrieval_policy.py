from __future__ import annotations

import re

from src.core.retrieval_policy_models import (
    RetrievalPolicyDecision,
    RetrievalPolicyInput,
)


class RetrievalPolicy:
    """
    Deterministic policy that decides whether a conversational turn
    should use RAG, memory, both, or neither.

    Important assumption for the current Ticket model:
    - domain, subdomain and product may come from the initial ticket
    - in later turns, only description and turn_id are expected to change

    Therefore:
    - initial turns can safely use metadata-based retrieval
    - later turns should avoid filter/hybrid retrieval when new information appears,
      because metadata may point to an older product or issue
    - later turns that require new retrieval should prefer semantic retrieval

    Conversation-level control such as closing, already closed, already escalated,
    max turns or max RAG calls is handled by ConversationController before this
    policy is executed.
    """

    def __init__(
        self,
        min_rich_description_words: int = 5,
        min_rich_description_chars: int = 30,
    ) -> None:
        self.min_rich_description_words = min_rich_description_words
        self.min_rich_description_chars = min_rich_description_chars

        self.clarification_patterns = {
            "explain it again",
            "explain it more simply",
            "what do you mean",
            "can you clarify",
            "clarify",
            "summarize",
            "summary",
            "step by step",
            "more detail",
            "i don't understand",
            "i do not understand",
            "explícamelo",
            "explicamelo",
            "explícalo",
            "explicalo",
            "más simple",
            "mas simple",
            "resume",
            "resúmelo",
            "resumelo",
            "paso a paso",
            "no lo entiendo",
            "puedes aclararlo",
            "puedes detallarlo",
        }

        self.follow_up_patterns = {
            "what should i do next",
            "what next",
            "and now",
            "then what",
            "does that also apply",
            "should i restart",
            "i tried that",
            "still happens",
            "still not working",
            "y ahora",
            "ahora qué",
            "ahora que",
            "qué hago ahora",
            "que hago ahora",
            "eso también aplica",
            "eso tambien aplica",
            "entonces lo reinicio",
            "he probado eso",
            "sigue igual",
            "sigue fallando",
        }

        self.problem_signals = {
            "error",
            "fail",
            "fails",
            "failed",
            "failing",
            "not working",
            "doesn't work",
            "does not work",
            "broken",
            "crash",
            "crashes",
            "drain",
            "drains",
            "overheat",
            "overheats",
            "hot",
            "warm",
            "refund",
            "cancel",
            "warranty",
            "delayed",
            "damaged",
            "can't login",
            "cannot login",
            "not charging",
            "issue",
            "problem",
            "fallo",
            "falla",
            "fallando",
            "no funciona",
            "roto",
            "rota",
            "se bloquea",
            "se calienta",
            "calienta",
            "batería",
            "bateria",
            "descarga",
            "devolver",
            "devolución",
            "devolucion",
            "reembolso",
            "cancelar",
            "garantía",
            "garantia",
            "tarde",
            "retrasado",
            "dañado",
            "dañada",
            "no carga",
            "problema",
        }

    def decide(self, policy_input: RetrievalPolicyInput) -> RetrievalPolicyDecision:
        """
        Decide whether the current turn should use RAG, memory, both, or neither.

        This policy assumes that conversation-control cases such as closing or
        forced escalation have already been handled by ConversationController.
        """

        ticket = policy_input.ticket

        description = self._normalize_text(ticket.description)

        has_memory = self._has_memory(policy_input.memory_context)
        has_metadata = self._has_valid_metadata(ticket)
        has_rich_description = self._has_rich_description(description)
        has_problem_signal = self._has_problem_signal(description)

        is_initial_turn = self._is_initial_turn(ticket.turn_id)

        is_clarification = self._is_clarification_turn(description)
        is_follow_up = self._is_follow_up_turn(description)

        if is_initial_turn:
            return self._decide_initial_turn(
                has_memory=has_memory,
                has_metadata=has_metadata,
                has_rich_description=has_rich_description,
            )

        return self._decide_later_turn(
            has_memory=has_memory,
            has_rich_description=has_rich_description,
            has_problem_signal=has_problem_signal,
            is_follow_up=is_follow_up,
            is_clarification=is_clarification,
        )

    def _decide_initial_turn(
        self,
        has_memory: bool,
        has_metadata: bool,
        has_rich_description: bool,
    ) -> RetrievalPolicyDecision:
        """
        Decide retrieval behavior for the initial ticket turn.

        In the initial turn, metadata is considered trustworthy because it belongs
        to the current ticket itself.
        """

        if has_metadata and has_rich_description:
            return RetrievalPolicyDecision(
                use_rag=True,
                use_memory=has_memory,
                is_initial_turn=True,
                retrieval_mode="hybrid",
                decision_type="metadata_and_description",
                reason="Initial turn with validated metadata and rich description. Hybrid retrieval is appropriate.",
            )

        if has_metadata and not has_rich_description:
            return RetrievalPolicyDecision(
                use_rag=True,
                use_memory=has_memory,
                is_initial_turn=True,
                retrieval_mode="filter",
                decision_type="metadata_only",
                reason="Initial turn with validated metadata but insufficient description for semantic retrieval.",
            )

        if not has_metadata and has_rich_description:
            return RetrievalPolicyDecision(
                use_rag=True,
                use_memory=has_memory,
                is_initial_turn=True,
                retrieval_mode="semantic",
                decision_type="description_only",
                reason="Initial turn with rich description but missing metadata. Semantic retrieval is appropriate.",
            )

        return RetrievalPolicyDecision(
            use_rag=False,
            use_memory=has_memory,
            is_initial_turn=True,
            retrieval_mode="none",
            decision_type="insufficient_information",
            reason="Initial turn without enough metadata or descriptive information to justify retrieval.",
        )

    def _decide_later_turn(
        self,
        has_memory: bool,
        has_rich_description: bool,
        has_problem_signal: bool,
        is_follow_up: bool,
        is_clarification: bool,
    ) -> RetrievalPolicyDecision:
        """
        Decide retrieval behavior for later conversational turns.

        In later turns, metadata may be stale because the current Ticket model
        does not update domain, subdomain or product per message.

        Therefore, when retrieval is needed in later turns, semantic retrieval is
        safer than filter or hybrid retrieval.
        """

        if is_follow_up and not has_problem_signal and not has_rich_description:
            return RetrievalPolicyDecision(
                use_rag=False,
                use_memory=has_memory,
                is_initial_turn=False,
                retrieval_mode="none",
                decision_type="follow_up",
                reason="Later turn appears to continue the previous conversation without adding enough new information for retrieval.",
            )

        if has_problem_signal and has_rich_description:
            return RetrievalPolicyDecision(
                use_rag=True,
                use_memory=has_memory,
                is_initial_turn=False,
                retrieval_mode="semantic",
                decision_type="problem_update",
                reason="Later turn adds new problem-related information. Semantic retrieval is used to avoid stale metadata filtering.",
            )

        if is_clarification:
            return RetrievalPolicyDecision(
                use_rag=False,
                use_memory=has_memory,
                is_initial_turn=False,
                retrieval_mode="none",
                decision_type="clarification",
                reason="The user is asking for clarification or reformulation of previous context.",
            )

        if has_rich_description:
            return RetrievalPolicyDecision(
                use_rag=True,
                use_memory=has_memory,
                is_initial_turn=False,
                retrieval_mode="semantic",
                decision_type="description_only",
                reason="Later turn contains a rich description. Semantic retrieval is safer because ticket metadata may refer to the initial issue.",
            )

        if has_problem_signal and has_memory:
            return RetrievalPolicyDecision(
                use_rag=False,
                use_memory=True,
                is_initial_turn=False,
                retrieval_mode="none",
                decision_type="follow_up",
                reason="Later turn contains a problem signal but not enough standalone description for reliable semantic retrieval. Memory should be used.",
            )

        return RetrievalPolicyDecision(
            use_rag=False,
            use_memory=has_memory,
            is_initial_turn=False,
            retrieval_mode="none",
            decision_type="insufficient_information",
            reason="Later turn does not contain enough new standalone information to justify retrieval.",
        )

    def _normalize_text(self, text: str | None) -> str:
        if not text:
            return ""

        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def _has_memory(self, memory_context: str | None) -> bool:
        return bool(memory_context and memory_context.strip())

    def _has_valid_metadata(self, ticket) -> bool:
        """
        Checks whether the ticket contains metadata that can support filter retrieval.

        This policy assumes metadata has already been validated by InputValidator.
        It only checks presence, not taxonomy correctness.
        """

        return all(
            [
                bool(getattr(ticket, "domain", None)),
                bool(getattr(ticket, "subdomain", None)),
                bool(getattr(ticket, "product", None)),
            ]
        )

    def _has_rich_description(self, description: str) -> bool:
        if not description:
            return False

        word_count = len(description.split())
        char_count = len(description)

        return (
            word_count >= self.min_rich_description_words
            or char_count >= self.min_rich_description_chars
        )

    def _has_problem_signal(self, description: str) -> bool:
        if not description:
            return False

        return any(signal in description for signal in self.problem_signals)

    def _is_initial_turn(self, turn_id: str | None) -> bool:
        """
        Detects whether the current turn should be treated as the initial ticket turn.

        Supported initial values:
        - None
        - "1"
        - "01"
        - "001"
        - "turn_1"
        - "turn_001"

        If turn_id is missing, the policy treats the input as an initial or
        standalone ticket for backwards compatibility with the existing pipeline.
        """

        if turn_id is None:
            return True

        normalized_turn_id = turn_id.strip().lower()

        if normalized_turn_id in {"", "1", "01", "001", "turn_1", "turn_01", "turn_001"}:
            return True

        numeric_part = re.sub(r"\D", "", normalized_turn_id)

        if numeric_part and int(numeric_part) == 1:
            return True

        return False

    def _is_clarification_turn(self, description: str) -> bool:
        if not description:
            return False

        return any(pattern in description for pattern in self.clarification_patterns)

    def _is_follow_up_turn(self, description: str) -> bool:
        if not description:
            return False

        return any(pattern in description for pattern in self.follow_up_patterns)
