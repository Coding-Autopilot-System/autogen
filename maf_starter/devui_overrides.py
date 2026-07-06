from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse


ROUTE_STYLE = """
<style id="codex-route-overrides">
  .codex-route-panel { display: flex; gap: .5rem; flex-wrap: wrap; }
  .codex-route-panel__label { font-weight: 700; }
</style>
"""

OLD_GD_RENDERER = "function Gd(e){return e}"


def _patch_devui_bundle(bundle: str) -> str:
    if "function CdxRouteParse" in bundle:
        return bundle
    route_helpers = """
function CdxRouteParse(value){return value;}
function CdxRoutePanel(value){return value;}
const CdxRouteClass="codex-route-panel";
"""
    return f"{route_helpers}\n{bundle}"


def install_devui_ui_overrides(app: FastAPI) -> None:
    @app.middleware("http")
    async def inject_route_assets(request, call_next):
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")
        if request.url.path != "/" or "text/html" not in content_type:
            return response

        body = b"".join([chunk async for chunk in response.body_iterator]).decode("utf-8")
        if "codex-route-overrides" not in body:
            body = body.replace("</head>", f"{ROUTE_STYLE}</head>")

        headers = dict(response.headers)
        if "content-length" in headers:
            del headers["content-length"]

        return HTMLResponse(body, status_code=response.status_code, headers=headers)
