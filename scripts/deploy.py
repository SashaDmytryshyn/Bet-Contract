from brownie import PlatformToken, BetContract, network
from scripts.helpful_scripts import get_account, deploy_mocks, get_contract
import yaml
import json
import os
import shutil


def deploy_bet_contract_and_platform_token(front_end_update=False):
    # requires brownie account to have been created
    # add these accounts to metamask by importing private key
    account = get_account()
    bet_contract = BetContract.deploy({"from": account})
    platform_token = PlatformToken.deploy({"from": account})

    if network.show_active() == "development":
        # launch contracts only for development (like mock price feeds)
        deploy_mocks()

    dict_of_allowed_tokens = {
        platform_token: get_contract("dai_usd_price_feed"),
    }
    add_allowed_tokens(bet_contract, dict_of_allowed_tokens, account)
    if front_end_update:
        update_front_end()
    return bet_contract, platform_token


def add_allowed_tokens(bet_contract, dict_of_allowed_tokens, account):
    for token in dict_of_allowed_tokens:
        add_tx = bet_contract.addAllowedTokens(token.address, {"from": account})
        print(token.address)
        print(bet_contract.allowedTokens(0) == token.address)
        add_tx.wait(1)
        set_tx = bet_contract.setPriceFeedContract(
            token.address,
            dict_of_allowed_tokens[token],
            False,
            {"from": account},
        )
        set_tx.wait(1)
        print("PRICE FEED FOR PLATFORM TOKEN:")
        print(dict_of_allowed_tokens[token])
        print(bet_contract.tokenPriceFeedMapping(token.address))
        print(
            bet_contract.tokenPriceFeedMapping(token.address)
            == dict_of_allowed_tokens[token]
        )
    # address doesnt matter since we have True for isChainToken
    set_txChain = bet_contract.setPriceFeedContract(
        account.address, get_contract("eth_usd_price_feed"), True, {"from": account}
    )
    set_txChain.wait(1)
    return bet_contract


def update_front_end():
    # Send the build folder
    copy_folders_to_front_end("./build", "./front_end/src/chain-info")

    # Sending the front end our config in JSON format
    with open("brownie-config.yaml", "r") as brownie_config:
        config_dict = yaml.load(brownie_config, Loader=yaml.FullLoader)
        with open("./front_end/src/brownie-config.json", "w") as brownie_config_json:
            json.dump(config_dict, brownie_config_json)
    print("Front end updated!")


def copy_folders_to_front_end(src, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def main():
    deploy_bet_contract_and_platform_token(front_end_update=True)
