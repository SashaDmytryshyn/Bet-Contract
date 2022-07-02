pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract PlatformToken is ERC20 {
    constructor() public ERC20("Platform Token", "PTK") {
        _mint(msg.sender, 1000000000000000000000000);
    }
}
