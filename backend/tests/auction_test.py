import pytest
from algokit_utils import (
    ApplicationClient,
    ApplicationSpecification,
    get_localnet_default_account,
)
from algosdk.v2client.algod import AlgodClient

from smart_contracts.auction import contract as auction_contract


@pytest.fixture(scope="session")
def auction_app_spec(algod_client: AlgodClient) -> ApplicationSpecification:
    return auction_contract.app.build(algod_client)


@pytest.fixture(scope="session")
def auction_client(
    algod_client: AlgodClient, auction_app_spec: ApplicationSpecification
) -> ApplicationClient:
    client = ApplicationClient(
        algod_client,
        app_spec=auction_app_spec,
        signer=get_localnet_default_account(algod_client),
    )
    client.create()
    return client


def test_create(auction_client: ApplicationClient) -> None:
    pass
