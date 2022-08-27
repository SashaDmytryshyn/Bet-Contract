// SPDX-License-Identifier: MIT
//used https://github.com/PatrickAlphaC/defi-stake-yield-brownie-freecode as a reference for some parts
pragma solidity 0.8.13;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract BetContract is Ownable {
    // mapping token address -> user address -> amount
    mapping(address => mapping(address => uint256)) public userAltBalances;
    mapping(address => uint256) public userCoreBalances;
    address[] public allowedTokens;
    address[] public altUsers;
    mapping(address => uint256) public uniqueTokensDeposited;
    mapping(address => address) public tokenPriceFeedMapping;
    address public chainTokenPriceFeed;

    //the recieve function takes care of users depositing the core chain token
    function depositTokens(uint256 _amount, address _token) public {
        require(_amount > 0, "Amount must be more than 0");
        require(tokenIsAllowed(_token), "Token is currently not allowed");
        //problem here is we have to pay gas for this transaction...will have to change it so user does this transaction.
        IERC20(_token).transferFrom(msg.sender, address(this), _amount);
        updateUniqueTokensDeposited(msg.sender, _token);
        userAltBalances[_token][msg.sender] =
            userAltBalances[_token][msg.sender] +
            _amount;
        if (uniqueTokensDeposited[msg.sender] == 1) {
            altUsers.push(msg.sender);
        }
    }

    //withdraw function for users to remove tokens from the platform
    function withdrawTokensAlt(uint256 _amount, address _token) public {
        require(_amount > 0, "Amount must be more than 0");
        require(tokenIsAllowed(_token), "Token is currently not allowed");
        //check if user has enough amount of token deposited
        require(userAltBalances[_token][msg.sender] >= _amount);
        //remove the amount the user has from the platform, then send it to them
        userAltBalances[_token][msg.sender] -= _amount;
        IERC20(_token).transfer(msg.sender, _amount);
    }

    //withdraw function for the platform token
    function withdrawTokensCore(uint256 _amount) public payable {
        require(_amount > 0, "Amount must be more than 0");
        //ensure user has enough funds
        require(userCoreBalances[msg.sender] >= _amount);
        //remove funds from platform and send to user
        userCoreBalances[msg.sender] -= _amount;
        payable(msg.sender).transfer(_amount);
    }

    function updateUniqueTokensDeposited(address _user, address _token)
        internal
    {
        if (userAltBalances[_token][_user] <= 0) {
            uniqueTokensDeposited[_user] = uniqueTokensDeposited[_user] + 1;
        }
    }

    function tokenIsAllowed(address _token) public view returns (bool) {
        for (
            uint256 allowedTokensIndex = 0;
            allowedTokensIndex < allowedTokens.length;
            allowedTokensIndex++
        ) {
            if (allowedTokens[allowedTokensIndex] == _token) {
                return true;
            }
        }
        return false;
    }

    function addAllowedTokens(address _token) public onlyOwner {
        allowedTokens.push(_token);
    }

    function setPriceFeedContract(
        address _token,
        address _priceFeed,
        bool isChainToken
    ) public onlyOwner {
        if (isChainToken) {
            chainTokenPriceFeed = _priceFeed;
        } else {
            tokenPriceFeedMapping[_token] = _priceFeed;
        }
    }

    //the receive takes care of supporting the chain token
    receive() external payable {
        userCoreBalances[msg.sender] += msg.value;
        uniqueTokensDeposited[msg.sender] += 1;
    }

    function getUserTotalValue(address _user) public view returns (uint256) {
        uint256 totalValue = 0;
        require(uniqueTokensDeposited[_user] > 0, "No tokens deposited!");
        //get value from the manually-added tokens
        if (allowedTokens.length > 0) {
            for (
                uint256 allowedTokensIndex = 0;
                allowedTokensIndex < allowedTokens.length;
                allowedTokensIndex++
            ) {
                totalValue =
                    totalValue +
                    getUserSingleTokenValue(
                        _user,
                        allowedTokens[allowedTokensIndex],
                        false
                    );
            }
        }
        //get value from the chain token
        totalValue =
            totalValue +
            getUserSingleTokenValue(_user, address(0), true);
        return totalValue;
    }

    function getUserSingleTokenValue(
        address _user,
        address _token,
        bool isChainToken
    ) public view returns (uint256) {
        if (isChainToken) {
            (uint256 price, uint256 decimals) = getTokenValue(_token, true);
            return ((userCoreBalances[_user] * price) / (10**decimals));
        } else {
            if (uniqueTokensDeposited[_user] <= 0) {
                return 0;
            }
            // price of the token * userAltBalances[_token][user]
            (uint256 price, uint256 decimals) = getTokenValue(_token, false);
            return // 10000000000000000000 ETH
            // ETH/USD -> 10000000000
            // 10 * 100 = 1,000
            ((userAltBalances[_token][_user] * price) / (10**decimals));
        }
    }

    function getTokenValue(address _token, bool isChainToken)
        public
        view
        returns (uint256, uint256)
    {
        // priceFeedAddress
        address priceFeedAddress;
        if (isChainToken) {
            priceFeedAddress = chainTokenPriceFeed;
        } else {
            priceFeedAddress = tokenPriceFeedMapping[_token];
        }
        AggregatorV3Interface priceFeed = AggregatorV3Interface(
            priceFeedAddress
        );
        (, int256 price, , , ) = priceFeed.latestRoundData();
        uint256 decimals = uint256(priceFeed.decimals());
        return (uint256(price), decimals);
    }

    //option for any user to create a bet? for now: onlyOwner and randNum bets
    //condNum: the number the random num achieved has to be higher for side 0 to win
    //expTime: time till the bet expires/concludes in seconds(?)
    //every bet needs to keep track of: sides, users on each side, amount users put on the bet (an either side)
    //total pool
    //store each Bet into a mapping ID->bet
    struct BetStruct {
        address[] side0Users;
        mapping(address => uint256) side0Balances;
        uint256 side0Total;
        address[] side1Users;
        mapping(address => uint256) side1Balances;
        uint256 side1Total;
        uint256 condNum;
        uint256 expTime;
        uint256 ID;
    }
    mapping(uint256 => BetStruct) public bets;

    function createBet(uint256 condNum, uint256 expTime) public onlyOwner {}

    //the same user that made this transaction should be the same user making the bet
    //meaning we can use sender.address to look at their userBalance
    function placeBet(
        uint256 betID,
        uint256 amount,
        address tokenAddress
    ) public {
        //BetStruct bet = bets[betID];
        //check if user has enough for amount of token
        //if so, update the bet to include them AFTER subtracting from their balance
    }
}
