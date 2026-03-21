from __future__ import annotations

import json
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from autogen_dashboard.dependencies import get_session_service
from autogen_dashboard.schemas import (
    HealthResponse,
    ProviderListResponse,
    RepoListResponse,
    SessionActionResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionDecisionRequest,
    SessionDetail,
    SessionListResponse,
    SessionMessageRequest,
    SessionRunRequest,
)
from autogen_dashboard.session_runner import SessionService
from autogen_starter.providers import ProviderConfigError


def create_app() -> FastAPI:
    app = FastAPI(title="AutoGen Dashboard", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    static_dir = Path(__file__).with_name("static")
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/healthz", response_model=HealthResponse)
    async def healthz() -> HealthResponse:
        return HealthResponse()

    @app.get("/api/providers", response_model=ProviderListResponse)
    async def api_providers(service: SessionService = Depends(get_session_service)) -> ProviderListResponse:
        return service.provider_statuses()

    @app.get("/api/repos", response_model=RepoListResponse)
    async def api_repos(service: SessionService = Depends(get_session_service)) -> RepoListResponse:
        return service.available_repos()

    @app.get("/api/sessions", response_model=SessionListResponse)
    async def api_list_sessions(service: SessionService = Depends(get_session_service)) -> SessionListResponse:
        return service.list_sessions()

    @app.post("/api/sessions", response_model=SessionCreateResponse)
    async def api_create_session(
        request: SessionCreateRequest,
        service: SessionService = Depends(get_session_service),
    ) -> SessionCreateResponse:
        if not request.task or not request.task.strip():
            raise HTTPException(status_code=400, detail="task is required for run creation.")
        if not request.repo_root or not request.repo_root.strip():
            raise HTTPException(status_code=400, detail="repo_root is required for run creation.")
        try:
            return await service.create_session(request)
        except ProviderConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/sessions/{session_id}", response_model=SessionDetail)
    async def api_get_session(
        session_id: str,
        service: SessionService = Depends(get_session_service),
    ) -> SessionDetail:
        try:
            return service.get_session(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/sessions/{session_id}/messages", response_model=SessionActionResponse)
    async def api_add_message(
        session_id: str,
        request: SessionMessageRequest,
        service: SessionService = Depends(get_session_service),
    ) -> SessionActionResponse:
        try:
            session = await service.append_message(session_id, request)
            return SessionActionResponse(session=session)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/sessions/{session_id}/approve", response_model=SessionActionResponse)
    async def api_approve(
        session_id: str,
        request: SessionDecisionRequest,
        service: SessionService = Depends(get_session_service),
    ) -> SessionActionResponse:
        try:
            session = await service.approve(session_id, request)
            return SessionActionResponse(session=session)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/sessions/{session_id}/reject", response_model=SessionActionResponse)
    async def api_reject(
        session_id: str,
        request: SessionDecisionRequest,
        service: SessionService = Depends(get_session_service),
    ) -> SessionActionResponse:
        try:
            session = await service.reject(session_id, request)
            return SessionActionResponse(session=session)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/sessions/{session_id}/run", response_model=SessionActionResponse)
    async def api_run(
        session_id: str,
        request: SessionRunRequest | None = None,
        service: SessionService = Depends(get_session_service),
    ) -> SessionActionResponse:
        try:
            session = await service.run_step(session_id, request)
            return SessionActionResponse(session=session)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ProviderConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/sessions/{session_id}/stop", response_model=SessionActionResponse)
    async def api_stop(
        session_id: str,
        service: SessionService = Depends(get_session_service),
    ) -> SessionActionResponse:
        try:
            session = await service.stop(session_id)
            return SessionActionResponse(session=session)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/sessions/{session_id}/cancel", response_model=SessionActionResponse)
    async def api_cancel(
        session_id: str,
        service: SessionService = Depends(get_session_service),
    ) -> SessionActionResponse:
        try:
            session = await service.cancel(session_id)
            return SessionActionResponse(session=session)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/sessions/{session_id}/retry", response_model=SessionActionResponse)
    async def api_retry(
        session_id: str,
        service: SessionService = Depends(get_session_service),
    ) -> SessionActionResponse:
        try:
            session = await service.retry(session_id)
            return SessionActionResponse(session=session)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/sessions/{session_id}/events")
    async def api_session_events(
        session_id: str,
        since_seq: int = 0,
        service: SessionService = Depends(get_session_service),
    ) -> StreamingResponse:
        try:
            service.get_session(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        async def event_stream():
            snapshot = service.get_session(session_id)
            cursor = since_seq or snapshot.event_count
            yield _sse_frame("snapshot", snapshot.model_dump(mode="json"), event_id=snapshot.event_count)
            async for event in service.stream_events(session_id, since_seq=cursor):
                yield _sse_frame(event.type, event.model_dump(mode="json"), event_id=event.seq)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.get("/", response_model=None)
    async def root():
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"status": "ok"}

    return app


def _sse_frame(event_name: str, payload: dict[str, object], event_id: int | str | None = None) -> str:
    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event_name}")
    lines.append(f"data: {json.dumps(payload, ensure_ascii=True)}")
    lines.append("")
    return "\n".join(lines) + "\n"


app = create_app()
