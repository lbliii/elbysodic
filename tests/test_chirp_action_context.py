from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest
from chirp.pages.actions import action, dispatch_action, load_actions


@dataclass(frozen=True, slots=True)
class RequestScopedProbe:
    marker: str


def test_chirp_page_actions_do_not_invoke_request_scoped_providers() -> None:
    @action("probe")
    def probe_action(probe: RequestScopedProbe) -> str:
        return probe.marker

    def request_scoped_provider(*, request: object) -> RequestScopedProbe:
        return RequestScopedProbe(marker=str(request))

    action_info = load_actions(_ActionModule(probe_action))[0]

    with pytest.raises(TypeError):
        asyncio.run(
            dispatch_action(
                action_info,
                path_params={},
                cascade_ctx={},
                service_providers={RequestScopedProbe: request_scoped_provider},
                form_data={"_action": "probe"},
            )
        )


class _ActionModule:
    def __init__(self, probe_action: object) -> None:
        self.probe_action = probe_action
