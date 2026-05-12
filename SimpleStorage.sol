// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleStorage {
    uint256 public value;
    address public owner;
    
    event ValueSet(uint256 newValue, address setter);
    
    constructor() {
        owner = msg.sender;
    }
    
    function set(uint256 _value) public {
        value = _value;
        emit ValueSet(_value, msg.sender);
    }
    
    function get() public view returns (uint256) {
        return value;
    }
}