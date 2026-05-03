from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage

from src.core.query_rewriter_models import QueryRewriterInput, QueryRewriterOutput
from src.core.config import GOOGLE_API_KEY


class QueryRewriterAgent:
    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.0):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name, temperature=temperature)
        self.structured_llm = self.llm.with_structured_output(
            QueryRewriterOutput)

    def rewrite(self, query_rewriter_input: QueryRewriterInput) -> QueryRewriterOutput:
        messages = self._build_messages(query_rewriter_input)
        result = self.structured_llm.invoke(messages)
        return result

    def _build_messages(self, query_rewriter_input: QueryRewriterInput) -> list[BaseMessage]:
        current_description = query_rewriter_input.current_description.strip()
        memory_context = query_rewriter_input.memory_context.strip()

        system_prompt = """
You rewrite customer support messages into one concise semantic search query.

Rules:
- Use only current message + memory.
- Do not answer, troubleshoot, classify, validate metadata, choose retrieval mode, decide RAG, or escalate.
- Do not invent facts.
- If current message contradicts memory, prioritize current message.
- Optimize for vector search.
- Output in English.
"""

        human_prompt = f"""
CURRENT USER MESSAGE:
{current_description}

MEMORY CONTEXT:
{memory_context}
"""

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]
