"""
    :module name: creators
    :module summary: endpoint classes that deal with data creation
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import logging
import secrets
import hashlib

from fastapi import status
from sqlalchemy.exc import IntegrityError

from . import BaseEndpointHandler
from .preprocessors import AuthorizationRequired
from ..services import RegisteredService
from ..models import (
        CredentialSet,
        AccountRecord,
        EndpointErrorMessage,
        EndpointInformationalMessage,
        EndpointResponse,
        CreateConcept,
        ConceptSimpleView,
        ConceptLinkRecord,
        EstablishLink,
        FollowRequest,
        LikeRequest
        )
from ..exceptions import (
        InvalidReferenceException,
        DuplicateRecordException,
        BaseIdeaBankAPIException,
        )

LOGGER = logging.getLogger(__name__)


class AccountCreationHandler(BaseEndpointHandler):
    """Endpoint handler dealing with account creation"""

    def _do_data_ops(self, request: CredentialSet):
        LOGGER.info("Securing new account credentials")
        secured_request = self._secure_payload(
                username=request.display_name,
                raw_pass=request.password
                )
        try:
            LOGGER.info("Creating new account record")
            with self.get_service(RegisteredService.ACCOUNTS_DS) as service:
                service.add_query(service.create_account(
                        username=secured_request.display_name,
                        hashed_password=secured_request.password_hash,
                        salt_value=secured_request.salt_value
                    ))
                service.exec_next()
                return service.results.one().display_name
        except IntegrityError as err:
            LOGGER.error(
                    "Attempted to add duplicate record: %s",
                    request.display_name
                    )
            raise DuplicateRecordException(
                    f"{request.display_name}"
                    ) from err

    def _secure_payload(self, username, raw_pass):
        salt = secrets.token_hex()
        password_hash = hashlib.sha256(
                f'{raw_pass}{salt}'.encode('utf-8')
                ).hexdigest()
        return AccountRecord(
                display_name=username,
                password_hash=password_hash,
                salt_value=salt
                )

    def _build_success_response(self, requested_data: str):
        LOGGER.info("Account for %s successfully created", requested_data)
        self._result = EndpointResponse(
                code=status.HTTP_201_CREATED,
                body=EndpointInformationalMessage(
                    msg=f'Account for {requested_data} successfully created'
                    )
                )

    def _build_error_response(self, exc: BaseIdeaBankAPIException):
        LOGGER.info("Account could not be created")
        if isinstance(exc, DuplicateRecordException):
            self._result = EndpointResponse(
                    code=status.HTTP_403_FORBIDDEN,
                    body=EndpointErrorMessage(
                        err_msg=f'Account not created: {str(exc)} not available'
                        )
                    )
        else:
            super()._build_error_response(exc)


class ConceptCreationHandler(AuthorizationRequired):
    """Endpoint handler dealing with concept creation"""

    def _do_data_ops(self, request: CreateConcept):
        LOGGER.info(
                "Creating concept record `%s` authored by `%s`",
                request.title,
                request.author
                )
        try:
            with self.get_service(RegisteredService.CONCEPTS_DS) as service:
                service.add_query(service.create_concept(
                        author=request.author,
                        title=request.title,
                        description=request.description,
                        diagram=request.diagram
                    ))
                service.exec_next()
                return ConceptSimpleView(
                        identifier=service.results.one().identifier,
                        thumbnail_url=service.share_item(
                            f'thumbnails/{request.author}/{request.title}'
                            )
                        )
        except IntegrityError as err:
            LOGGER.error(
                    "Cannot create duplicate concept `%s/%s`",
                    request.author,
                    request.title
                    )
            raise DuplicateRecordException(
                    f'{request.author}/{request.title}'
                    ) from err

    def _build_success_response(self, requested_data: ConceptSimpleView):
        LOGGER.info("Successfully created the concept `%s`", requested_data.identifier)
        self._result = EndpointResponse(
                code=status.HTTP_201_CREATED,
                body=requested_data
                )

    def _build_error_response(self, exc: BaseIdeaBankAPIException):
        LOGGER.error("Could not create the concept `%s`", str(exc))
        if isinstance(exc, DuplicateRecordException):
            self._result = EndpointResponse(
                    code=status.HTTP_403_FORBIDDEN,
                    body=EndpointErrorMessage(
                        err_msg=f'{str(exc)} is not available'
                        )
                    )
        else:
            super()._build_error_response(exc)


class ConceptLinkingHandler(AuthorizationRequired):
    """Endpoint handler dealing with concept linking"""

    def _do_data_ops(self, request: EstablishLink):
        LOGGER.info(
                "Establishing a link between `%s` and `%s`",
                request.ancestor,
                request.descendant
                )
        if request.ancestor == request.descendant:
            LOGGER.error("Cannot link a concept to itself")
            raise InvalidReferenceException(
                    "Self referential links not allowed"
                    )
        try:
            with self.get_service(RegisteredService.CONCEPTS_DS) as service:
                service.add_query(service.link_existing_concept(
                    parent_identifier=request.ancestor,
                    child_identifier=request.descendant
                    ))
                service.exec_next()
                result = service.results.one()
                return ConceptLinkRecord(
                        ancestor=result.ancestor,
                        descendant=result.descendant
                        )
        except IntegrityError as err:
            LOGGER.error(
                    "Could not establish link between `%s` and `%s`",
                    request.ancestor,
                    request.descendant
                    )
            if 'not present in table' in str(err):
                raise InvalidReferenceException(
                        "Both concepts must exist to link them"
                        ) from err
            if 'already exists' in str(err):
                raise DuplicateRecordException(
                    f"A link already exists between {request.ancestor} and {request.descendant}"
                    ) from err
            raise

    def _build_success_response(self, requested_data: ConceptLinkRecord):
        LOGGER.info("Link successfully created.")
        self._result = EndpointResponse(
                code=status.HTTP_201_CREATED,
                body=requested_data
                )

    def _build_error_response(self, exc: BaseIdeaBankAPIException):
        LOGGER.error("Link could not be created.")
        if isinstance(exc, (DuplicateRecordException, InvalidReferenceException)):
            self._result = EndpointResponse(
                    code=status.HTTP_403_FORBIDDEN,
                    body=EndpointErrorMessage(
                        err_msg=str(exc)
                        )
                    )
        else:
            super()._build_error_response(exc)


class StartFollowingAccountHandler(AuthorizationRequired):
    """Endpoint handler dealing with creating following records"""

    def _do_data_ops(self, request: FollowRequest):
        LOGGER.info(
                "Creating the follow record: %s <- %s",
                request.followee,
                request.follower
                )
        if request.follower == request.followee:
            LOGGER.error("Cannot follow self")
            raise InvalidReferenceException(
                    "Cannot follow yourself. "
                    "You'll need to make real connections."
                    )
        try:
            with self.get_service(RegisteredService.ENGAGE_DS) as service:
                service.add_query(service.insert_following(
                    request.follower,
                    request.followee
                    ))
                service.exec_next()
                result = service.results.one()
                return EndpointInformationalMessage(
                        msg=f"{result.follower} is now following {result.followee}"
                        )
        except IntegrityError as err:
            LOGGER.error(
                    "Could not create follow record between `%s` and `%s`",
                    request.followee,
                    request.follower
                    )
            if 'not present in table' in str(err):
                raise InvalidReferenceException(
                        "Both accounts must exist to follow or be followed"
                        ) from err
            if 'already exists' in str(err):
                raise DuplicateRecordException(
                    f"A following exists between {request.follower} and {request.followee}"
                    ) from err
            raise

    def _build_success_response(self, requested_data: EndpointInformationalMessage):
        self._result = EndpointResponse(
                code=status.HTTP_201_CREATED,
                body=requested_data
                )

    def _build_error_response(self, exc: BaseIdeaBankAPIException):
        if isinstance(exc, (InvalidReferenceException, DuplicateRecordException)):
            self._result = EndpointResponse(
                    code=status.HTTP_403_FORBIDDEN,
                    body=EndpointErrorMessage(
                        err_msg=str(exc)
                        )
                    )
        else:
            super()._build_error_response(exc)


class StartLikingConceptHandler(AuthorizationRequired):
    """Endpoint handler dealing with creating liking records"""

    def _do_data_ops(self, request: LikeRequest):
        LOGGER.info(
                "Creating the likes record: %s <- %s",
                request.concept_liked,
                request.user_liking
                )
        try:
            with self.get_service(RegisteredService.ENGAGE_DS) as service:
                service.add_query(service.insert_liking(
                    request.user_liking,
                    request.concept_liked
                    ))
                service.exec_next()
                result = service.results.one()
                return EndpointInformationalMessage(
                        msg=f"{result.display_name} now likes the concept of {result.concept_id}"
                        )
        except IntegrityError as err:
            LOGGER.error(
                    "Could not create likes record between `%s` and `%s`",
                    request.concept_liked,
                    request.user_liking
                    )
            if 'not present in table' in str(err):
                raise InvalidReferenceException(
                        "Both the account and concept must exist"
                        ) from err
            if 'already exists' in str(err):
                raise DuplicateRecordException(
                    f"A liking exists between {request.concept_liked} and {request.user_liking}"
                    ) from err
            raise

    def _build_success_response(self, requested_data: EndpointInformationalMessage):
        self._result = EndpointResponse(
                code=status.HTTP_201_CREATED,
                body=requested_data
                )

    def _build_error_response(self, exc: BaseIdeaBankAPIException):
        if isinstance(exc, (InvalidReferenceException, DuplicateRecordException)):
            self._result = EndpointResponse(
                    code=status.HTTP_403_FORBIDDEN,
                    body=EndpointErrorMessage(
                        err_msg=str(exc)
                        )
                    )
        else:
            super()._build_error_response(exc)
