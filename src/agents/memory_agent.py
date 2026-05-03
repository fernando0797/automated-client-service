from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage

from src.core.memory_models import MemoryUpdateInput, ConversationMemory
from src.core.config import GOOGLE_API_KEY


class MemoryAgent:
    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.0):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
        )

        self.structured_llm = self.llm.with_structured_output(
            ConversationMemory)

    def update_memory(self, memory_update_input: MemoryUpdateInput) -> ConversationMemory:
        messages = self._build_messages(memory_update_input)
        result = self.structured_llm.invoke(messages)
        return result

    def _build_messages(self, memory_update_input: MemoryUpdateInput) -> list[BaseMessage]:
        ticket_description = memory_update_input.ticket.description
        context = memory_update_input.summary.context
        problem = memory_update_input.summary.problem
        previous_memory = (
            memory_update_input.previous_memory.memory
            if memory_update_input.previous_memory
            and memory_update_input.previous_memory.memory.strip()
            else None
        )
        response = memory_update_input.response.response
        response_type = memory_update_input.response.resolution_type

        system_prompt = """
You are a Conversation Memory Agent for a customer support chatbot.

Your only task is to create or update the conversation memory after the current support turn.

There may or may not be previous conversation memory:
- If previous memory is provided, update it with the current turn.
- If previous memory is not provided, create the first memory from the current turn.

The memory will be injected into the next turn, so it must help the system continue the conversation without losing context.

Rules:
- Keep the active user problem clear.
- Preserve useful previous information when previous memory exists.
- If the current turn contradicts previous memory, prioritize the current turn.
- Capture relevant user-confirmed facts.
- Track what the user has already tried only when the user explicitly says they tried it.
- Track what the assistant has suggested, but do not confuse suggestions with completed user actions.
- Include unresolved issues or pending next steps when relevant.
- Do not answer the customer.
- Do not generate new troubleshooting steps.
- Do not mention internal pipeline details, agents, prompts, tools, RAG, retrieval, chunks, or system decisions.
- Do not store generic support knowledge unless it was part of the assistant response and is useful for continuity.
- Remove unnecessary repetition.
- Remove outdated details when the current turn makes them irrelevant.
- Keep the memory concise, factual, and useful.
- Write the memory in English.

Return only the conversation memory.
""".strip()

        if previous_memory:
            human_prompt = f"""
PREVIOUS CONVERSATION MEMORY:
{previous_memory}

CURRENT USER MESSAGE:
{ticket_description}

CURRENT PROBLEM:
{problem}

CURRENT CONTEXT:
{context}

ASSISTANT RESPONSE:
{response}

RESPONSE TYPE:
{response_type}

TASK:
Update the previous conversation memory using the current turn.

The updated memory should preserve still-relevant information from the previous memory and incorporate the new information from this turn.

Do not copy the previous memory verbatim if it can be improved, shortened, or updated.
Do not include anything that is no longer relevant.
""".strip()
        else:
            human_prompt = f"""
CURRENT USER MESSAGE:
{ticket_description}

CURRENT PROBLEM:
{problem}

CURRENT CONTEXT:
{context}

ASSISTANT RESPONSE:
{response}

RESPONSE TYPE:
{response_type}

TASK:
Create the first conversation memory from this turn.

The memory should capture the active issue, relevant user-confirmed facts, assistant suggestions, and unresolved state if applicable.
""".strip()

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]
