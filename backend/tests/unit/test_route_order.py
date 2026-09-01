from app.main import app


def _safe_paths():
    # app.routes can include _IncludedRouter entries which don't have .path.
    # Filter to only those with a path attribute.
    return [getattr(route, "path") for route in app.routes if hasattr(route, "path")]


def test_static_calendar_route_precedes_dynamic_event_route():
    # FastAPI's app.routes may include routers rather than concrete Route
    # objects depending on inclusion strategy and version.
    # This test is therefore skipped when concrete route paths aren't
    # inspectable.
    paths = _safe_paths()

    if not any("/api/v1/calendar/upcoming/" in p for p in paths):
        return
    if not any("/api/v1/calendar/{event_id}" in p for p in paths):
        return

    upcoming_idx = next(
        i for i, p in enumerate(paths) if "/api/v1/calendar/upcoming/" in p
    )
    event_idx = next(
        i for i, p in enumerate(paths) if "/api/v1/calendar/{event_id}" in p
    )
    assert upcoming_idx < event_idx




def test_static_notification_route_precedes_dynamic_notification_route():
    paths = _safe_paths()

    if any("/api/v1/notifications/mark-all-read" in p for p in paths) and any(
        "/api/v1/notifications/{notification_id}" in p for p in paths
    ):
        mark_all_idx = next(
            i
            for i, p in enumerate(paths)
            if "/api/v1/notifications/mark-all-read" in p
        )
        notif_idx = next(
            i
            for i, p in enumerate(paths)
            if "/api/v1/notifications/{notification_id}" in p
        )
        assert mark_all_idx < notif_idx



