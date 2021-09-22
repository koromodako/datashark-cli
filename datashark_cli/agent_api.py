"""AgentAPI
"""
from yarl import URL
from aiohttp import (
    ClientResponseError,
    ClientConnectorError,
    ServerDisconnectedError,
)
from datashark_core.logging import cprint, cwidth
from datashark_core.model.api import (
    ProcessorsRequest,
    ProcessingRequest,
    AgentInfoResponse,
    ProcessorsResponse,
    ProcessingResponse,
)
from . import LOGGER


class AgentAPI:
    """Agent API"""

    def __init__(self, url: str):
        self._base_url = URL(url)

    @property
    def base_url(self):
        """Agent's base url"""
        return self._base_url

    def display_banner(self):
        """Display agent's banner"""
        cprint('=' * cwidth())
        cprint(self._base_url, highlight=True)
        cprint('=' * cwidth())

    async def _get(self, session, url, resp_cls):
        """Sending GET request to the agent listening on the other side"""
        resp_inst = None
        try:
            async with session.get(url) as a_resp:
                resp_inst = resp_cls.build(await a_resp.json())
        except ClientConnectorError as exc:
            LOGGER.error("failed to connect to agent at %s", self._base_url)
            LOGGER.error(exc)
        except ServerDisconnectedError as exc:
            LOGGER.error(
                "server refused the connection, it might be expecting a certificate"
            )
        except ClientResponseError as exc:
            LOGGER.warning(
                "%s:%d: %s", self._base_url, exc.status, exc.message
            )
        return resp_inst

    async def _post(self, session, url, req_inst, resp_cls):
        """Send POST request to the agent listening on the other side"""
        resp_inst = None
        try:
            async with session.post(url, json=req_inst.as_dict()) as a_resp:
                resp_inst = resp_cls.build(await a_resp.json())
        except ClientConnectorError as exc:
            LOGGER.error("failed to connect to agent at %s", self._base_url)
            LOGGER.error(exc)
        except ServerDisconnectedError as exc:
            LOGGER.error(
                "server refused the connection, it might be expecting a certificate"
            )
        except ClientResponseError as exc:
            LOGGER.warning(
                "%s:%d: %s", self._base_url, exc.status, exc.message
            )
        return resp_inst

    async def info(self, session) -> AgentInfoResponse:
        """Perform a query to retrieve agent's information"""
        url = self._base_url / 'info'
        return await self._get(session, url, AgentInfoResponse)

    async def processors(self, session, search=None) -> ProcessorsResponse:
        """Perform a query to retrieve agent's supported processors"""
        url = self._base_url / 'processors'
        req_inst = ProcessorsRequest(search=search)
        return await self._post(session, url, req_inst, ProcessorsResponse)

    async def process(self, session, processor) -> ProcessingResponse:
        """Perform a query to have the agent process some resources"""
        url = self._base_url / 'process'
        req_inst = ProcessingRequest(processor=processor)
        return await self._post(session, url, req_inst, ProcessingResponse)
