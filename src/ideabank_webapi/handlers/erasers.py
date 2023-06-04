"""
    :module name: erasers
    :module summary: A collection of handlers that remove data records
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging

from fastapi import status

from .preprocessors import AuthorizationRequired
from ..services import RegisteredService
from ..models import (
    UnfollowRequest,
    EndpointInformationalMessage,
    EndpointResponse
        )
from ..exceptions import BaseIdeaBankAPIException

LOGGER = logging.getLogger(__name__)


class StopFollowingAccountHandler(AuthorizationRequired):
    """Endpoint handler dealing with removing following records"""

    def _do_data_ops(self, request: UnfollowRequest):
        LOGGER.info(
                "Removing the following record %s <- %s",
                request.followee,
                request.follower
                )
        with self.get_service(RegisteredService.ENGAGE_DS) as service:
            service.add_query(service.revoke_following(
                follower=request.follower,
                followee=request.followee
                ))
            service.exec_next()

        return EndpointInformationalMessage(
                msg=f"{request.follower} is no longer following {request.followee}"
                )

    def _build_error_response(self, exc: BaseIdeaBankAPIException):  # pylint:disable=useless-parent-delegation
        super()._build_error_response(exc)

    def _build_success_response(self, requested_data: EndpointInformationalMessage):
        self._result = EndpointResponse(
                code=status.HTTP_200_OK,
                body=requested_data
                )
