from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage

from src.core.summary_models import SummaryInput, SummaryOutput
from src.core.config import GOOGLE_API_KEY


class SummaryAgent:
    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.0):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
        )

        self.structured_llm = self.llm.with_structured_output(SummaryOutput)

    def summarize(self, summary_input: SummaryInput) -> SummaryOutput:
        messages = self._build_messages(summary_input)
        result = self.structured_llm.invoke(messages)
        return result

    def _build_messages(self, summary_input: SummaryInput) -> list[BaseMessage]:
        system_prompt = """
You are an internal support summarization component.

Your task is to produce a concise structured summary of the current support case.

Use the current ticket description as the source of truth for the customer's latest message.
Use the retrieved context only as supporting information.
Use memory context only if it is provided and relevant to the current case.

Return:
- problem: what issue the user is experiencing
- context: relevant contextual information that helps understand or resolve the case
- intent: what the user is trying to achieve or obtain in this turn

Field limits:
- problem: maximum 500 characters
- context: maximum 1000 characters
- intent: maximum 300 characters

Rules:
- Be faithful to the provided information.
- Do not invent facts, policies, guarantees, technical steps, or escalation rules.
- Do not answer the customer.
- Do not mention internal components such as agents, RAG, chunks, retrieval, metadata, or knowledge base.
- Do not expose internal reasoning.
- Keep the summary concise but informative.
- When filling the context field, synthesize the most relevant information from retrieved context and memory context if present.
- Do not copy the retrieved context verbatim.
- If memory context conflicts with the current ticket description, prioritize the current ticket description.
""".strip()

        human_prompt = self._build_human_prompt(summary_input)

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

    def _build_human_prompt(self, summary_input: SummaryInput) -> str:
        ticket_description = summary_input.ticket.description.strip()
        built_context = summary_input.built_context.context_text.strip()
        memory_context = (summary_input.memory_context or "").strip()

        sections: list[str] = [
            f"""
CURRENT TICKET DESCRIPTION

{ticket_description}
""".strip(),
            f"""
RETRIEVED CONTEXT

{built_context}
""".strip(),
        ]

        if memory_context:
            sections.append(
                f"""
MEMORY CONTEXT

{memory_context}
""".strip()
            )

        return "\n\n".join(sections)
