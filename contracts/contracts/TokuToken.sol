// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TokuToken {
    string public name = "Toku Token";
    string public symbol = "TOKU";
    uint8 public decimals = 18;

    mapping(address => uint256) public balanceOf;
    mapping(address => int256) public virtueScore; // 徳スコア（マイナス値可能）
    mapping(address => bool) public pendingCommunityService; // トイレ掃除ペナルティフラグ

    event TokenMinted(address indexed to, uint256 amount, string reason);
    event TokenSlashed(address indexed target, uint256 amount, string reason);

    // AI/DAO判定によるトークン付与
    function mint(address _to, uint256 _amount, string memory _reason) public {
        balanceOf[_to] += _amount;
        virtueScore[_to] += int256(_amount);
        emit TokenMinted(_to, _amount, _reason);
    }

    // 不正検知時のスラッシング（没収 ＋ ペナルティ付与）
    function slash(address _target, uint256 _amount, string memory _reason) public {
        if (balanceOf[_target] >= _amount) {
            balanceOf[_target] -= _amount;
        } else {
            balanceOf[_target] = 0;
        }
        virtueScore[_target] -= int256(_amount * 2); // ペナルティ倍率
        pendingCommunityService[_target] = true;     // 物理奉仕作業のフラグオン
        emit TokenSlashed(_target, _amount, _reason);
    }
}