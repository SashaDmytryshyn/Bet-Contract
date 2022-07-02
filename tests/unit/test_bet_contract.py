from brownie import network, exceptions
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    DECIMALS,
)
import pytest
from scripts.deploy import deploy_bet_contract_and_platform_token

# this tests tokenIsAllowed,addAllowedTokens functions
# it also tests the onlyOwner attribute on addAllowedTokens
def test_token_allowed():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    bet_contract, platform_token = deploy_bet_contract_and_platform_token()
    # Act
    bet_contract.addAllowedTokens(platform_token.address, {"from": account})
    # Assert
    assert (
        bet_contract.tokenIsAllowed(platform_token.address, {"from": account}) == True
    )
    assert bet_contract.allowedTokens(0) == platform_token.address
    with pytest.raises(exceptions.VirtualMachineError):
        bet_contract.addAllowedTokens(platform_token.address, {"from": non_owner})


# this tests that when the user sends funds to the contract, and the contract keeps track of how much the user send (with no unexpected behaviour)
def test_receive():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    bet_contract, platform_token = deploy_bet_contract_and_platform_token()
    # Act
    account.transfer(bet_contract, "1.243 ether")
    # Assert
    assert bet_contract.balance() == 1243000000000000000
    assert bet_contract.userCoreBalances(account.address) == 1243000000000000000
    assert bet_contract.uniqueTokensDeposited(account.address) == 1


# here we add/approve depositing of the platform token, and test that we can deposit it just fine
# this tests updateUniqueTokensDeposited,depositTokens, and some functions from our platform token
def test_deposit(deposit_amount):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    bet_contract, platform_token = deploy_bet_contract_and_platform_token()
    # Act
    bet_contract.addAllowedTokens(platform_token.address, {"from": account})
    platform_token.transfer(non_owner.address, deposit_amount, {"from": account})
    platform_token.approve(bet_contract.address, deposit_amount, {"from": non_owner})
    bet_contract.depositTokens(
        deposit_amount, platform_token.address, {"from": non_owner}
    )
    # Assert
    assert (
        bet_contract.userAltBalances(platform_token.address, non_owner.address)
        == deposit_amount
    )
    assert bet_contract.uniqueTokensDeposited(non_owner.address) == 1
    assert bet_contract.altUsers(0) == non_owner.address


# tests setPriceFeedContract
def test_set_price_feed():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    bet_contract, platform_token = deploy_bet_contract_and_platform_token()
    # Act
    bet_contract.addAllowedTokens(platform_token.address, {"from": account})
    bet_contract.setPriceFeedContract(
        platform_token.address, non_owner.address, False, {"from": account}
    )  # This tests if we can set price feed for a new token
    bet_contract.setPriceFeedContract(
        platform_token.address, non_owner.address, True, {"from": account}
    )  # This tests if we can set price feed for the chain token
    # Assert
    assert bet_contract.chainTokenPriceFeed() == non_owner.address
    assert (
        bet_contract.tokenPriceFeedMapping(platform_token.address) == non_owner.address
    )


# tests getUserTotalValue,getUserSingleTokenValue,getTokenValue
def test_get_user_token_values():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    bet_contract, platform_token = deploy_bet_contract_and_platform_token()
    # Act
    # from calling deploy_bet_contract_and_platform_token, platform_token and chain token
    # should already have price feeds via add_allowed_tokens
    # non_owner should start with 100 eth, send 1 eth to contract
    non_owner.transfer(bet_contract, "1 ether")
    # Assert
    assert bet_contract.getTokenValue(account, True) == (2000000000000000000000, 18)
    assert bet_contract.getUserSingleTokenValue(
        non_owner, account, True
    ) == 1000000000000000000 * 2000000000000000000000 / (10**DECIMALS)
    # need to change this test so that we also deposit a non-chain token and test if getUserTotalValue is still correct
    assert bet_contract.getUserTotalValue(
        non_owner, {"from": account}
    ) == 1000000000000000000 * 2000000000000000000000 / (10**DECIMALS)
