from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage

from src.core.response_models import ResponseInput, ResponseOutput
from src.core.config import GOOGLE_API_KEY


class ResponseAgent:
    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.0):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
        )

        self.structured_llm = self.llm.with_structured_output(ResponseOutput)

    def generate_response(self, response_input: ResponseInput) -> ResponseOutput:
        messages = self._build_messages(response_input)
        result = self.structured_llm.invoke(messages)
        return result

    def _build_messages(self, response_input: ResponseInput) -> list[BaseMessage]:
        system_prompt = """
You are a customer support response agent.

Your task is to generate the final response that will be shown to the customer.

Use the current ticket description as the source of truth for the customer's latest message.
If a structured summary is provided, use it as the main interpretation of the case.
If no structured summary is provided, answer using the current ticket description and any relevant memory context.
Use memory context only when it is relevant to the current ticket description.

Return:
- response: the final message to the customer
- tone: the tone used in the response
- resolution_type: the type of resolution provided
- requires_escalation: whether the case should be escalated to human support or another support channel
- confidence: estimated confidence in the response, between 0.0 and 1.0
- escalation_channel: the recommended escalation channel if escalation is required

Rules:
- Be faithful to the provided information.
- Do not invent policies, guarantees, technical steps, escalation rules, or contact channels.
- Do not mention internal components such as agents, summaries, RAG, chunks, retrieval, metadata, memory, or knowledge base.
- Do not expose internal reasoning.
- Write the response as if speaking directly to the customer.
- Be clear, helpful, and concise.
- The response field must be under 3000 characters.
- Provide actionable next steps when possible.
- If the available information is insufficient, ask for the most relevant missing information or recommend escalation.
- If requires_escalation is false, escalation_channel must be "none".
- If requires_escalation is true, choose the most appropriate theoretical channel from: "phone", "email", "human_chat", or "support_ticket".
- Do not actually perform the escalation.
- If the issue can be solved with troubleshooting, provide ordered troubleshooting steps.
- If more information is needed from the user, ask only for the most relevant missing details.
- If memory context conflicts with the current ticket description, prioritize the current ticket description.
""".strip()

        human_prompt = self._build_human_prompt(response_input)

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

    def _build_human_prompt(self, response_input: ResponseInput) -> str:
        ticket_description = response_input.ticket.description.strip()
        summary = response_input.summary
        memory_context = (response_input.memory_context or "").strip()

        sections: list[str] = [
            f"""
CURRENT TICKET DESCRIPTION

{ticket_description}
""".strip()
        ]

        if summary is not None:
            sections.append(
                f"""
STRUCTURED SUMMARY

Problem:
{summary.problem}

Context:
{summary.context}

Intent:
{summary.intent}
""".strip()
            )

        if memory_context:
            sections.append(
                f"""
MEMORY CONTEXT

{memory_context}
""".strip()
            )

        return "\n\n".join(sections)
