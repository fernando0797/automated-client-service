from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.api.dependencies import AppServices, build_app_services, check_database_connection, get_api_db_session, get_api_status, build_support_graph_runner
from src.api.schemas import ChatRequest, ChatResponse
from src.core.request_models import Ticket


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.services = build_app_services()
    yield


app = FastAPI(title="Support Chatbot API", version="0.1.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=[
                   "http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def get_app_services(request: Request) -> AppServices:
    return request.app.state.services


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Support Chatbot API is running",
        "docs": "/docs",
        "health": "/health"}


@app.get("/health")
def health() -> dict[str, str]:
    return get_api_status()


@app.get("/health/db")
def health_db(session: Session = Depends(get_api_db_session)) -> dict[str, str | bool]:
    database_ok = check_database_connection(session)

    return {
        "status": "ok",
        "database": database_ok}


@app.get("/health/services")
def health_services(services: AppServices = Depends(get_app_services)) -> dict[str, str | bool]:
    return {
        "status": "ok",
        "services_loaded": services is not None,
        "retriever_tool_loaded": services.retriever_tool is not None}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, session: Session = Depends(get_api_db_session), services: AppServices = Depends(get_app_services)) -> ChatResponse:
    ticket = Ticket(
        ticket_id=request.ticket_id,
        turn_id=request.turn_id,
        source=request.source,
        description=request.description,
        domain=request.domain,
        subdomain=request.subdomain,
        product=request.product)

    runner = build_support_graph_runner(session=session, app_services=services)

    output = runner.run(ticket)

    response = output.response

    retrieval_used = None
    retrieval_mode = None

    if output.retrieval_output is not None:
        retrieval_used = output.retrieval_output.called
        retrieval_mode = output.retrieval_output.mode_used

    requires_escalation = getattr(response, "requires_escalation", False)
    should_close = getattr(response, "should_close", False)

    return ChatResponse(
        ticket_id=output.ticket.ticket_id,
        turn_id=output.ticket.turn_id,
        response=response.response,
        status=output.conversation_state_after.status,
        requires_escalation=requires_escalation,
        should_close=should_close,
        retrieval_used=retrieval_used,
        retrieval_mode=retrieval_mode,
        initial_route=output.initial_route,
        nodes_executed=output.nodes_executed)
