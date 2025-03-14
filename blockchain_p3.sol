//Specifies the version of Solidity used for the contract
pragma solidity ^0.4.11;

contract hadcoin_ico { //Defines the smart contract named hadcoin_ico

    // public variables can be accessed from outside of contract as well
    // private variables can only be accessed inside the contract
    // Introducing the maximum number of Hadcoins available for sale
    uint public max_hadcoins = 1000000;

    // Introducing the USD to Hadcoins conversion rate
    uint public usd_to_hadcoins = 1000;

    // Introducing the total number of Hadcoins that have been bought by the investors
    uint public total_hadcoins_bought = 0;

    // Mapping from the investor address to its equity in Hadcoins and USD
    mapping(address => uint) equity_hadcoins;
    mapping(address => uint) equity_usd;

    // A modifier is a reusable piece of code that can be attached to a function to change or restrict its behavior.
    // Modifiers are typically used to enforce conditions before executing a function.
    // The _ placeholder represents the function body that uses the modifier. After the condition is checked, the function body is executed.
    // Checking if an investor can buy Hadcoins
    modifier can_buy_hadcoins(uint usd_invested) {
        require(usd_invested * usd_to_hadcoins + total_hadcoins_bought <= max_hadcoins);
        _;
    }

    // Functions marked with external can only be called from outside the contract (e.g., by other contracts or externally by users via transactions).
    // These functions cannot be called internally within the same contract unless this.functionName() is used.
    // constant: A keyword that makes a function read-only, meaning it cannot modify the state of the contract.
    // Getting the equity in Hadcoins of an investor
    function equity_in_hadcoins(address investor) external constant returns (uint) {
        return equity_hadcoins[investor];
    }

    // Getting the equity in USD of an investor
    function equity_in_usd(address investor) external constant returns (uint) {
        return equity_usd[investor];
    }

    // Buying Hadcoins
    function buy_hadcoins(address investor, uint usd_invested) external 
    can_buy_hadcoins(usd_invested) {
        uint hadcoins_bought = usd_invested * usd_to_hadcoins;
        equity_hadcoins[investor] += hadcoins_bought;
        equity_usd[investor] = equity_hadcoins[investor] / usd_to_hadcoins;
        total_hadcoins_bought += hadcoins_bought;
    }

    // Selling Hadcoins
    function sell_hadcoins(address investor, uint hadcoins_sold) external {
        equity_hadcoins[investor] -= hadcoins_sold;
        equity_usd[investor] = equity_hadcoins[investor] / usd_to_hadcoins;
        total_hadcoins_bought -= hadcoins_sold;
    }

}