from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from autogen_dashboard.session_runner import SessionService
from autogen_dashboard.session_store import SessionStore
from autogen_starter.config import Settings, load_settings


@dataclass(frozen=True)
class DashboardContext:
    settings: Settings
    store: SessionStore
    service: SessionService


def build_dashboard_context(
    *,
    settings: Settings | None = None,
    store: SessionStore | None = None,
) -> DashboardContext:
    current_settings = settings or load_settings()
    current_store = store or SessionStore(current_settings.state_dir / "sessions")
    service = SessionService(settings=current_settings, store=current_store)
    return DashboardContext(settings=current_settings, store=current_store, service=service)


@lru_cache(maxsize=1)
def get_dashboard_context() -> DashboardContext:
    return build_dashboard_context()


def get_settings() -> Settings:
    return get_dashboard_context().settings


def get_store() -> SessionStore:
    return get_dashboard_context().store


def get_session_service() -> SessionService:
    return get_dashboard_context().service
