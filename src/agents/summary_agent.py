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
        ticket = summary_input.ticket
        built_context = summary_input.built_context.context_text
        memory_context = summary_input.memory_context

        system_prompt = """
You are an internal support summarization component.

Your task is to produce a concise structured summary of the current support case.

Return:
- problem: what issue the user is experiencing
- context: relevant contextual information that helps understand or resolve the case
- intent: what the user is trying to achieve or obtain in this turn

Rules:
- Be faithful to the provided information.
- Do not invent facts.
- Use the retrieved context only as supporting information.
- If memory context is empty or missing, ignore it.
- Keep the summary concise but informative.
""".strip()

        human_prompt = f"""
description:
{ticket.description}
The following information was retrieved from the knowledge base and should be used as the main support context for the summary:
{built_context}

MEMORY CONTEXT
{memory_context if memory_context else "None"}
""".strip()

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]
