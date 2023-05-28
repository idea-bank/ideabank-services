"""Tests for creator handlers"""

import pytest
from unittest.mock import patch
from ideabank_webapi.handlers import EndpointHandlerStatus
from ideabank_webapi.handlers.creators import AccountCreationHandler
from ideabank_webapi.services import RegisteredService, AccountsDataService, QueryService
from ideabank_webapi.models import (
        CredentialSet,
        EndpointInformationalMessage,
        EndpointErrorMessage,
        IdeaBankSchema
)
from ideabank_webapi.exceptions import BaseIdeaBankAPIException

from sqlalchemy import create_engine
from fastapi import status


@patch.object(QueryService, 'ENGINE', create_engine('sqlite:///:memory:', echo=True))
class TestAccountCreationHandler:
    TEST_ACCOUNTS = [
        CredentialSet(display_name=f'username{i}', password=f'password{i}')
        for i in range(1, 6)
            ]

    def setup_method(self):
        self.handler = AccountCreationHandler()
        self.handler.use_service(RegisteredService.ACCOUNTS_DS, AccountsDataService())
        print(
                self.handler.get_service(RegisteredService.ACCOUNTS_DS).ENGINE
                )

    def _init_test_db(self):
        print(
                self.handler.get_service(RegisteredService.ACCOUNTS_DS).ENGINE
                )
        IdeaBankSchema.metadata.create_all(
                self.handler.get_service(RegisteredService.ACCOUNTS_DS).ENGINE
                )
        for user in self.TEST_ACCOUNTS:
            self.handler.receive(user)
            self.handler._status = EndpointHandlerStatus.IDLE

    @pytest.mark.parametrize("creds", [
        CredentialSet(display_name=f'username{i}', password=f'password{i}')
        for i in range(6, 8)
        ])
    def test_create_new_account(self, creds):
        self._init_test_db()
        self.handler.receive(creds)
        assert self.handler.status == EndpointHandlerStatus.COMPLETE
        assert self.handler.result.code == status.HTTP_201_CREATED
        assert self.handler.result.body == EndpointInformationalMessage(
                msg=f'Account for {creds.display_name} successfully created'
                )

    @pytest.mark.parametrize("creds", [
        CredentialSet(display_name=f'username{i}', password=f'password{i}')
        for i in range(1, 4)
        ])
    def test_attempt_to_create_duplicate_account(self, creds):
        self._init_test_db()
        self.handler.receive(creds)
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_403_FORBIDDEN
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg=f'Account not created: {creds.display_name} not available'
                )

    @patch.object(
            AccountCreationHandler,
            '_do_data_ops',
            side_effect=BaseIdeaBankAPIException("Really obscure error")
        )
    def test_a_really_messed_up_scenario(self, mock_data_ops):
        self.handler.receive(CredentialSet(
            display_name='unluckyuser',
            password='unluckypassword'
            ))
        mock_data_ops.assert_called_once()
        assert self.handler.status == EndpointHandlerStatus.ERROR
        assert self.handler.result.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert self.handler.result.body == EndpointErrorMessage(
                err_msg='Really obscure error'
                )
