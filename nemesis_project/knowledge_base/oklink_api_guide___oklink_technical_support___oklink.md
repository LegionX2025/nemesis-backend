# OKLink API guide | OKLink technical support | OKLink
Source: https://www.oklink.com/docs/en/

OKLink API guide | OKLink technical support | OKLink
NAV
Explorer
Change Log
Explorer
Change Log
中文
Developer tools
Contract verification
Verify contract source code
Get contract source code verification results
Verify proxy contract
Get proxy contract verification results
Get verified contract's ABI and source code
Contract verification plugin
Contract verification using Hardhat
Contract verification using foundry
Contract verification using truffle
Developer tools
Retrieve detailed information on address and token authorizations. Utilize API tools for domain risk detection, on-chain transaction broadcasting, and contract verification for both proxy and standard contracts.
Contract verification
Source code verification provides a way for projects to open source their smart contract code for end users to inspect and verify that it does what it claims to do and improve the transparency.
Endpoints of the "Contract verification" module support submitting contract source code for contract verification, verifying proxy contracts, and querying the contract ABI and source code of already verified contracts.
Verify contract source code
By uploading the contract source code, OKLink explorer will match the compiled contract bytecode with the bytecode on the blockchain and display it on the contract page of the explorer.
You can use this endpoint to quickly verify contracts and improve verification efficiency. The average processing time for contract verification is between 30-60 seconds.
Consumption per query 0
HTTP Request
POST /api/v5/explorer/contract/verify-source-code
Request Example
POST /api/v5/explorer/contract/verify-source-code
body
{
"chainShortName":"ETH",
"contractAddress":"0x9Dca580D2c8B8e19e9d77345a5b4C2820B25b386",
"contractName":"HelloWorld",
"sourceCode":"pragma solidity ^0.7.6;↵contract HelloWorl {↵ string public greet = 'Hello Worl!';↵}",
"codeFormat":"solidity-single-file",
"compilerVersion":"v0.7.6+commit.7338295f",
"optimization":"1",
"optimizationRuns":"200",
"contractAbi":"0xfce353f66162630000000000000000000000000",
"evmVersion":"tangerineWhistle",
"viaIr":false,
"libraryInfo":[
{
"libraryName":"libraryName1",
"libraryAddress":"0xCfE28868F6E0A24b7333D22D8943279e76aC2cdc"
},
{
"libraryName":"libraryName2",
"libraryAddress":"0xCfE28868F6E0A24b7333D22D8943279e76aC2cdc"
},
{
"libraryName":"libraryName3",
"libraryAddress":"0xCfE28868F6E0A24b7333D22D8943279e76aC2cdc"
}
]
}
Request Parameters
Parameter
Type
Required
Description
chainShortName
String
Yes
The abbreviated name of the blockchain network
contractAddress
String
Yes
Contract address
contractName
String
Yes
Contract name
sourceCode
String
Yes
Source code of the contract.
If your contract uses "imports", you will need to concatenate the code into one file (otherwise known as "flattening") as we do not support "imports" in separate files.
You can use Solidity flatteners like
SolidityFlattery
(by
@DaveAppleton
)
codeFormat
String
Yes
Code format, we support
solidity-single-file
,
solidity-standard-json-input
,
vyper
compilerVersion
String
No
Compiler version used, e.g.,
v0.7.6+commit.7338295f
,
vyper:0.2.11
.
You can check the supported compiler versions for contract verification in the OKLink Explorer under the
Verify Contract
section
When the codeFormat is
solidity-standard-json-input
, it is optional; otherwise, it is required.
optimization
String
No
Whether optimization was used when compiling the contract,
0
for no optimization,
1
if optimization was used
When the codeFormat is
solidity-standard-json-input
, it is optional; otherwise, it is required.
optimizationRuns
String
No
The number of runs if optimization was used, e.g., 200
contractAbi
String
No
Contract ABI
evmVersion
String
No
EVM version of contract compilation, leave blank for default compiler, specify if others such as
tangerineWhistle
,
spuriousDragon
,
byzantium
licenseType
String
No
Open source license type, leave blank for default
No License
viaIr
Bol
No
Whether to introduce an IR-based code generator, should be consistent with your compiling setting;
true
/
false
,
false
by default
libraryInfo
Array
No
Library info used in contract.
The libraryName and libraryAddress must be matched one by one.
We support up to 10 different libraries.
> libraryName
String
No
Library name
> libraryAddress
String
No
Library address, e.g., 0xCfE28868F6E0A24b7333D22D8943279e76aC2cdc
Response Example
{
"code"
:
"0"
,
"msg"
:
""
,
"data"
:
[
"eb5c06099d3841359d398541166343fe"
]
}
Response Parameters
Parameter
Type
Description
guid
String
A GUID is returned upon successful submission, which can be used to query the verification result
Get contract source code verification results
After submitting the source code verification, you can query the result with the GUID returned.
Consumption per query 0
HTTP Request
POST /api/v5/explorer/contract/check-verify-result
Request Example
POST /api/v5/explorer/contract/check-verify-result
body
{
"chainShortName":"ETH",
"guid":"eb5c06099d3841359d398541166343fe"
}
Request Parameters
Parameter
Type
Required
Description
chainShortName
String
Yes
The abbreviated name of the blockchain network
guid
String
Yes
Query the source code verification result with the GUID returned
Response Example
{
"code"
:
"0"
,
"msg"
:
""
,
"data"
:
[
"Success"
]
}
Response Parameters
Parameter
Type
Description
result
String
Contract source code verification result
Success
,
Fail
,
Pending
Verify proxy contract
Verify whether a proxy contract implements the contract as expected.
Consumption per query 0
HTTP Request
POST /api/v5/explorer/contract/verify-proxy-contract
Request Example
POST /api/v5/explorer/contract/verify-proxy-contract
body
{
"chainShortName": "ETH",
"proxyContractAddress": "0xfeee12d53ddb7ce61ee467ddf7243212a953174a",
"expectedImplementation": "0x0ecbefc71524068cf18f9d4e50d787e134ee70b8"
}
Request Parameters
Parameter
Type
Required
Description
chainShortName
String
Yes
The abbreviated name of the blockchain network
proxyContractAddress
String
Yes
Proxy contract address
expectedImplementation
String
No
Verify whether the implementation contract for the proxy contract is this address
Response Example
{
"code"
:
"0"
,
"msg"
:
""
,
"data"
:
[
"4f2e75682f75410f958c0a3bbf754358"
]
}
Response Parameters
Parameter
Type
Description
guid
String
A GUID is returned upon successful submission, which can be used to query the verification result
Get proxy contract verification results
After submitting the proxy contract verification, you can query the result with the GUID returned.
Consumption per query 0
HTTP Request
POST /api/v5/explorer/contract/check-proxy-verify-result
Request Example
POST /api/v5/explorer/contract/check-proxy-verify-result
body
{
"chainShortName":"ETH",
"guid":"4f2e75682f75410f958c0a3bbf754358"
}
Request Parameters
Parameter
Type
Required
Description
chainShortName
String
Yes
The abbreviated name of the blockchain network
guid
String
Yes
Query the proxy contract verification result with the GUID returned
Response Example
{
"code"
:
"0"
,
"msg"
:
"The proxy's (0x826427966fb2e7edee940c5d99b7d66062faef2e) implementation contract is found at 0xd4a2dca4e03713d5bf7d2173237058466a9c1be4 and is successfully updated."
,
"data"
:
[]
}
Response Parameters
Parameter
Type
Description
result
String
Proxy contract verification result.
If the verification is successful, return the address of the implementation contract.
If the verification fails, return "A corresponding implementation contract was unfortunately not detected for the proxy address."
Get verified contract's ABI and source code
Query the contract ABI, source code and other basic information of the verified contract, or query the implementation contract address information of the verified proxy contract.
Consumption per query 0
HTTP Request
GET /api/v5/explorer/contract/verify-contract-info
Request Example
/api/v5/explorer/contract/verify-contract-info?chainShortName=ETH&contractAddress=0xcF80631b469A54dcba8c8ee1aF84505f496ed248
Request Parameters
Parameter
Type
Required
Description
chainShortName
String
Yes
The abbreviated name of the blockchain network
contractAddress
String
Yes
Contract address
Response Example
{
"code"
:
"0"
,
"msg"
:
""
,
"data"
:
[
{
"sourceCode"
:
"// proxy.sol - execute actions atomically through the proxy's identity
\r\n\r\n
// Copyright (C) 2017
DappHub, LLC
\r\n\r\n
// This program is free software: you can redistribute it and/or modify
\r\n
// it under the terms of the GNU General Public License as published by
\r\n
// the Free Software Foundation, either version 3 of the License, or
\r\n
// (at your option) any later version.
\r\n\r\n
// This program is distributed in the hope that it will be useful,
\r\n
// but WITHOUT ANY WARRANTY; without even the implied warranty of
\r\n
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the
\r\n
// GNU General Public License for more details.
\r\n\r\n
// You should have received a copy of the GNU General Public License
\r\n
// along with this program.
If not, see <http://www.gnu.org/licenses/>.
\r\n\r\n
pragma solidity ^0.4.23;
\r\n\r\n
contract DSAuthority {
\r\n
function canCall(
\r\n
address src, address dst, bytes4 sig
\r\n
) public view returns (bool);
\r\n
}
\r\n\r\n
contract DSAuthEvents {
\r\n
event LogSetAuthority (address indexed authority);
\r\n
event LogSetOwner
(address indexed owner);
\r\n
}
\r\n\r\n
contract DSAuth is DSAuthEvents {
\r\n
DSAuthority
public
authority;
\r\n
address
public
owner;
\r\n\r\n
constructor() public {
\r\n
owner = msg.sender;
\r\n
emit LogSetOwner(msg.sender);
\r\n
}
\r\n\r\n
function setOwner(address owner_)
\r\n
public
\r\n
auth
\r\n
{
\r\n
owner = owner_;
\r\n
emit LogSetOwner(owner);
\r\n
}
\r\n\r\n
function setAuthority(DSAuthority authority_)
\r\n
public
\r\n
auth
\r\n
{
\r\n
authority = authority_;
\r\n
emit LogSetAuthority(authority);
\r\n
}
\r\n\r\n
modifier auth {
\r\n
require(isAuthorized(msg.sender, msg.sig));
\r\n
_;
\r\n
}
\r\n\r\n
function isAuthorized(address src, bytes4 sig) internal view returns (bool) {
\r\n
if (src == address(this)) {
\r\n
return true;
\r\n
} else if (src == owner) {
\r\n
return true;
\r\n
} else if (authority == DSAuthority(0)) {
\r\n
return false;
\r\n
} else {
\r\n
return authority.canCall(src, this, sig);
\r\n
}
\r\n
}
\r\n
}
\r\n\r\n
contract DSNote {
\r\n
event LogNote(
\r\n
bytes4
indexed
sig,
\r\n
address
indexed
guy,
\r\n
bytes32
indexed
foo,
\r\n
bytes32
indexed
bar,
\r\n
uint
wad,
\r\n
bytes
fax
\r\n
) anonymous;
\r\n\r\n
modifier note {
\r\n
bytes32 foo;
\r\n
bytes32 bar;
\r\n\r\n
assembly {
\r\n
foo := calldataload(4)
\r\n
bar := calldataload(36)
\r\n
}
\r\n\r\n
emit LogNote(msg.sig, msg.sender, foo, bar, msg.value, msg.data);
\r\n\r\n
_;
\r\n
}
\r\n
}
\r\n\r\n
// DSProxy
\r\n
// Allows code execution using a persistant identity This can be very
\r\n
// useful to execute a sequence of atomic actions. Since the owner of
\r\n
// the proxy can be changed, this allows for dynamic ownership models
\r\n
// i.e. a multisig
\r\n
contract DSProxy is DSAuth, DSNote {
\r\n
DSProxyCache public cache;
// global cache for contracts
\r\n\r\n
constructor(address _cacheAddr) public {
\r\n
require(setCache(_cacheAddr));
\r\n
}
\r\n\r\n
function() public payable {
\r\n
}
\r\n\r\n
// use the proxy to execute calldata _data on contract _code
\r\n
function execute(bytes _code, bytes _data)
\r\n
public
\r\n
payable
\r\n
returns (address target, bytes32 response)
\r\n
{
\r\n
target = cache.read(_code);
\r\n
if (target == 0x0) {
\r\n
// deploy contract & store its address in cache
\r\n
target = cache.write(_code);
\r\n
}
\r\n\r\n
response = execute(target, _data);
\r\n
}
\r\n\r\n
function execute(address _target, bytes _data)
\r\n
public
\r\n
auth
\r\n
note
\r\n
payable
\r\n
returns (bytes32 response)
\r\n
{
\r\n
require(_target != 0x0);
\r\n\r\n
// call contract in current context
\r\n
assembly {
\r\n
let succeeded := delegatecall(sub(gas, 5000), _target, add(_data, 0x20), mload(_data), 0, 32)
\r\n
response := mload(0)
// load delegatecall output
\r\n
switch iszero(succeeded)
\r\n
case 1 {
\r\n
// throw if delegatecall failed
\r\n
revert(0, 0)
\r\n
}
\r\n
}
\r\n
}
\r\n\r\n
//set new cache
\r\n
function setCache(address _cacheAddr)
\r\n
public
\r\n
auth
\r\n
note
\r\n
returns (bool)
\r\n
{
\r\n
require(_cacheAddr != 0x0);
// invalid cache address
\r\n
cache = DSProxyCache(_cacheAddr);
// overwrite cache
\r\n
return true;
\r\n
}
\r\n
}
\r\n\r\n
// DSProxyFactory
\r\n
// This factory deploys new proxy instances through build()
\r\n
// Deployed proxy addresses are logged
\r\n
contract DSProxyFactory {
\r\n
event Created(address indexed sender, address indexed owner, address proxy, address cache);
\r\n
mapping(address=>bool) public isProxy;
\r\n
DSProxyCache public cache = new DSProxyCache();
\r\n\r\n
// deploys a new proxy instance
\r\n
// sets owner of proxy to caller
\r\n
function build() public returns (DSProxy proxy) {
\r\n
proxy = build(msg.sender);
\r\n
}
\r\n\r\n
// deploys a new proxy instance
\r\n
// sets custom owner of proxy
\r\n
function build(address owner) public returns (DSProxy proxy) {
\r\n
proxy = new DSProxy(cache);
\r\n
emit Created(msg.sender, owner, address(proxy), address(cache));
\r\n
proxy.setOwner(owner);
\r\n
isProxy[proxy] = true;
\r\n
}
\r\n
}
\r\n\r\n
// DSProxyCache
\r\n
// This global cache stores addresses of contracts previously deployed
\r\n
// by a proxy. This saves gas from repeat deployment of the same
\r\n
// contracts and eliminates blockchain bloat.
\r\n\r\n
// By default, all proxies deployed from the same factory store
\r\n
// contracts in the same cache. The cache a proxy instance uses can be
\r\n
// changed.
The cache uses the sha3 hash of a contract's bytecode to
\r\n
// lookup the address
\r\n
contract DSProxyCache {
\r\n
mapping(bytes32 => address) cache;
\r\n\r\n
function read(bytes _code) public view returns (address) {
\r\n
bytes32 hash = keccak256(_code);
\r\n
return cache[hash];
\r\n
}
\r\n\r\n
function write(bytes _code) public returns (address target) {
\r\n
assembly {
\r\n
target := create(0, add(_code, 0x20), mload(_code))
\r\n
switch iszero(extcodesize(target))
\r\n
case 1 {
\r\n
// throw if contract failed to deploy
\r\n
revert(0, 0)
\r\n
}
\r\n
}
\r\n
bytes32 hash = keccak256(_code);
\r\n
cache[hash] = target;
\r\n
}
\r\n
}"
,
"contractName"
:
"DSProxy"
,
"compilerVersion"
:
"v0.4.23+commit.124ca40d"
,
"optimization"
:
"1"
,
"optimizationRuns"
:
"200"
,
"contractAbi"
:
"[{
\"
constant
\"
:false,
\"
inputs
\"
:[{
\"
indexed
\"
:false,
\"
name
\"
:
\"
owner_
\"
,
\"
type
\"
:
\"
address
\"
}],
\"
name
\"
:
\"
setOwner
\"
,
\"
outputs
\"
:[],
\"
payable
\"
:false,
\"
stateMutability
\"
:
\"
nonpayable
\"
,
\"
type
\"
:
\"
function
\"
},{
\"
constant
\"
:false,
\"
inputs
\"
:[{
\"
indexed
\"
:false,
\"
name
\"
:
\"
_target
\"
,
\"
type
\"
:
\"
address
\"
},{
\"
indexed
\"
:false,
\"
name
\"
:
\"
_data
\"
,
\"
type
\"
:
\"
bytes
\"
}],
\"
name
\"
:
\"
execute
\"
,
\"
outputs
\"
:[{
\"
name
\"
:
\"
response
\"
,
\"
type
\"
:
\"
bytes32
\"
}],
\"
payable
\"
:true,
\"
stateMutability
\"
:
\"
payable
\"
,
\"
type
\"
:
\"
function
\"
},{
\"
constant
\"
:false,
\"
inputs
\"
:[{
\"
indexed
\"
:false,
\"
name
\"
:
\"
_code
\"
,
\"
type
\"
:
\"
bytes
\"
},{
\"
indexed
\"
:false,
\"
name
\"
:
\"
_data
\"
,
\"
type
\"
:
\"
bytes
\"
}],
\"
name
\"
:
\"
execute
\"
,
\"
outputs
\"
:[{
\"
name
\"
:
\"
target
\"
,
\"
type
\"
:
\"
address
\"
},{
\"
name
\"
:
\"
response
\"
,
\"
type
\"
:
\"
bytes32
\"
}],
\"
payable
\"
:true,
\"
stateMutability
\"
:
\"
payable
\"
,
\"
type
\"
:
\"
function
\"
},{
\"
constant
\"
:true,
\"
inputs
\"
:[],
\"
name
\"
:
\"
cache
\"
,
\"
outputs
\"
:[{
\"
name
\"
:
\"\"
,
\"
type
\"
:
\"
address
\"
}],
\"
payable
\"
:false,
\"
stateMutability
\"
:
\"
view
\"
,
\"
type
\"
:
\"
function
\"
},{
\"
constant
\"
:false,
\"
inputs
\"
:[{
\"
indexed
\"
:false,
\"
name
\"
:
\"
authority_
\"
,
\"
type
\"
:
\"
address
\"
}],
\"
name
\"
:
\"
setAuthority
\"
,
\"
outputs
\"
:[],
\"
payable
\"
:false,
\"
stateMutability
\"
:
\"
nonpayable
\"
,
\"
type
\"
:
\"
function
\"
},{
\"
constant
\"
:true,
\"
inputs
\"
:[],
\"
name
\"
:
\"
owner
\"
,
\"
outputs
\"
:[{
\"
name
\"
:
\"\"
,
\"
type
\"
:
\"
address
\"
}],
\"
payable
\"
:false,
\"
stateMutability
\"
:
\"
view
\"
,
\"
type
\"
:
\"
function
\"
},{
\"
constant
\"
:false,
\"
inputs
\"
:[{
\"
indexed
\"
:false,
\"
name
\"
:
\"
_cacheAddr
\"
,
\"
type
\"
:
\"
address
\"
}],
\"
name
\"
:
\"
setCache
\"
,
\"
outputs
\"
:[{
\"
name
\"
:
\"\"
,
\"
type
\"
:
\"
bool
\"
}],
\"
payable
\"
:false,
\"
stateMutability
\"
:
\"
nonpayable
\"
,
\"
type
\"
:
\"
function
\"
},{
\"
constant
\"
:true,
\"
inputs
\"
:[],
\"
name
\"
:
\"
authority
\"
,
\"
outputs
\"
:[{
\"
name
\"
:
\"\"
,
\"
type
\"
:
\"
address
\"
}],
\"
payable
\"
:false,
\"
stateMutability
\"
:
\"
view
\"
,
\"
type
\"
:
\"
function
\"
},{
\"
constant
\"
:false,
\"
inputs
\"
:[{
\"
indexed
\"
:false,
\"
name
\"
:
\"
_cacheAddr
\"
,
\"
type
\"
:
\"
address
\"
}],
\"
payable
\"
:false,
\"
stateMutability
\"
:
\"
nonpayable
\"
,
\"
type
\"
:
\"
constructor
\"
},{
\"
constant
\"
:false,
\"
payable
\"
:true,
\"
stateMutability
\"
:
\"
payable
\"
,
\"
type
\"
:
\"
fallback
\"
},{
\"
constant
\"
:false,
\"
inputs
\"
:[{
\"
indexed
\"
:true,
\"
name
\"
:
\"
sig
\"
,
\"
type
\"
:
\"
bytes4
\"
},{
\"
indexed
\"
:true,
\"
name
\"
:
\"
guy
\"
,
\"
type
\"
:
\"
address
\"
},{
\"
indexed
\"
:true,
\"
name
\"
:
\"
foo
\"
,
\"
type
\"
:
\"
bytes32
\"
},{
\"
indexed
\"
:true,
\"
name
\"
:
\"
bar
\"
,
\"
type
\"
:
\"
bytes32
\"
},{
\"
indexed
\"
:false,
\"
name
\"
:
\"
wad
\"
,
\"
type
\"
:
\"
uint256
\"
},{
\"
indexed
\"
:false,
\"
name
\"
:
\"
fax
\"
,
\"
type
\"
:
\"
bytes
\"
}],
\"
name
\"
:
\"
LogNote
\"
,
\"
payable
\"
:false,
\"
type
\"
:
\"
event
\"
},{
\"
constant
\"
:false,
\"
inputs
\"
:[{
\"
indexed
\"
:true,
\"
name
\"
:
\"
authority
\"
,
\"
type
\"
:
\"
address
\"
}],
\"
name
\"
:
\"
LogSetAuthority
\"
,
\"
payable
\"
:false,
\"
type
\"
:
\"
event
\"
},{
\"
constant
\"
:false,
\"
inputs
\"
:[{
\"
indexed
\"
:true,
\"
name
\"
:
\"
owner
\"
,
\"
type
\"
:
\"
address
\"
}],
\"
name
\"
:
\"
LogSetOwner
\"
,
\"
payable
\"
:false,
\"
type
\"
:
\"
event
\"
}]"
,
"evmVersion"
:
"Default"
,
"licenseType"
:
"No License (None)"
,
"libraryInfo"
:
""
,
"proxy"
:
"0"
,
"implementation"
:
""
,
"swarmSource"
:
"bzzr://e498874c9ba9e75028e0c84f1b1d83b2dad5de910c59b837b32e5a190794c5e1"
}
]
}
Response Parameters
Parameter
Type
Description
sourceCode
String
Source code of the contract
contractName
String
Contract name
compilerVersion
String
Compiler version used
optimization
String
Whether optimization was used when compiling the contract,
0
for no optimization,
1
if optimization was used
optimizationRuns
String
The number of runs if optimization was used
contractAbi
String
Contract ABI
evmVersion
String
EVM version of contract compilation
licenseType
String
Open source license type
libraryInfo
Array
Library info used in contract
> libraryName
String
Library name
> libraryAddress
String
Library address, e.g., 0xCfE28868F6E0A24b7333D22D8943279e76aC2cdc
proxy
String
Whether it is a proxy contract,
0
means it is not a proxy contract,
1
means it is a proxy contract
implementation
String
The implementation contract address of the proxy contract
swarmSource
String
Swarm hash of contract source code
Contract verification plugin
OKLink supports contract verification using third-party plugins such as hardhat and truffle and foundry, greatly improving your contract verification efficiency.
The supported chains include ETH, XLAYER, XLAYER_TESTNET, BSC, POLYGON, AVAXC, FTM, OP, ARBITRUM, LINEA, MANTA, CANTO, BASE, SCROLL, OPBNB, POLYGON_ZKEVM, SEPOLIA_TESTNET, GOERLI_TESTNET, AMOY_TESTNET, MUMBAI_TESTNET, POLYGON_ZKEVM_TESTNET
Contract verification using Hardhat
Method 1 (recommended): Verify by
@okxweb3/hardhat-explorer-verify
plugin
1、Install the Plugin: To install this plugin in your Hardhat project, use the following command:
npm install @okxweb3/hardhat-explorer-verify
2、Configure Hardhat: In your Hardhat configuration file (usually
hardhat.config.js
or
hardhat.config.ts
), import and configure the plugin. Ensure your network configuration and API keys are correctly set.
Example：
import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import '@okxweb3/hardhat-explorer-verify';
// Import the plugin
const config: HardhatUserConfig = {
solidity: "0.8.24",
sourcify: {
enabled: true,
},
networks: {
xlayer: {
url: "https://xlayerrpc.example.com",
accounts: ["<Your Wallet Private Key>"],
},
},
etherscan: {
apiKey: '...'
},
okxweb3explorer: {
customChains: [
{
network: "Fractal Bitcoin Mainnet",
chainId: 70000061,
urls: {
apiURL: "https://www.oklink.com/api/v5/explorer/contract/verify-source-code-plugin/FRACTAL",
browserURL: "https://www.oklink.com",
}
}
]
}
};
export default config;
Custom chains can be configured based on the chains supported in openAPI
https://www.oklink.com/docs/zh/#quickstart-guide-list-of-supported-chains)
.
customChains: [{
network: "chainName",
chainId: {chainId},
urls: {
apiURL: "https://www.oklink.com/api/v5/explorer/contract/verify-source-code-plugin/{chainShortName}",
browserURL: "https://www.oklink.com",
}}]
3、Verify Contracts: After deploying the contracts, use Hardhat to run the verification script. This typically involves running a specific Hardhat task that automatically fetches contract data and submits it to the OKLink blockchain explorer for verification.
Example command:
npx hardhat okverify --network xlayer <Your Contract Address>
4、View Verification Results: Once verification is successful, you can view the verification status and the contract code on the OKLink blockchain explorer.
5、Verify TransparentUpgradeableProxy Contract
Example command:
npx hardhat okverify --network xlayer --contract <Contract>:<Name> --proxy <address>
--proxy
: mention it's a proxy contract address.
Note: If using 897 Contract, don't add
--proxy
. Directly use
npx hardhat okverify --network xlayer --contract <Contract>:<Name>
You can view detailed usage and instructions in
https://github.com/okx/hardhat-explorer-verify
Take the ETH chain as an example:
module.exports = {
...
etherscan: {
customChains: [
{
network: "eth",
chainId: 1,
urls: {
apiURL: "https://www.oklink.com/api/v5/explorer/contract/verify-source-code-plugin/eth",
browserURL: "https://www.oklink.com",
}
}
]
}
};
Method 2: Verify by making the following modifications to the
hardhat.config.js
file:
Set the network to the blockchain network you have added.
Set the chainId to the ID of the chain.
Set the apiURL in the urls to https://www.oklink.com/api/v5/explorer/contract/verify-source-code-plugin/{chainShortName}, you can find the {chainShortName} of different chains
here
, and set the browserURL to https://www.oklink.com.
Contract verification using foundry
Apply for OKLink API key: https://www.oklink.com/docs/en/#quickstart-guide-getting-started
Verify a contract with the forge verify-contract command. You must provide:
the contract address
the contract name or the path to the contract
:
verify-url
OKLink verify API url: https://www.oklink.com/api/v5/explorer/contract/verify-source-code-plugin/{chainShortName},
{chainShortName} is the short name of the chain, you can see the short name of the supported chain at
here
, explorerUrl is https://www.oklink.com
example：
forge verify-contract <the_contract_address>
src/MyToken.sol:MyToken
--verifier oklink
--verifier-url https://www.oklink.com/api/v5/explorer/contract/verify-source-code-plugin/eth
Check verification result
It is recommended to use the --watch flag along with verify-contract command in order to poll for the verification result.
If the --watch flag was not supplied, you can check the verification status with the forge verify-check command:
example：
forge verify-check --chain 11155111 --verifier oklink --verifier-url https://www.oklink.com/api/explorer/v1/contract/verify/async/api/ethsepolia <GUID>
Contract verification using truffle
Take the ETH chain as an example:
plugins: ['truffle-plugin-verify']
oklinkVerify: {
provider: () => new HDWalletProvider(privateKey, infuraUrl),
// Localhost (default: none)
gas: gasAmount,
network_id: 1,
verify: {
apiUrl: 'https://www.oklink.com/api/v5/explorer/contract/verify-source-code-plugin/eth@truffle',
explorerUrl: 'https://www.oklink.com/',
}
},
To verify a contract using
truffle plugin
, you need to add the following content to the module.exports module in the configuration file:
Set the network_id to the ID of the chain.
Set the apiURL in the urls to https://www.oklink.com/api/v5/explorer/contract/verify-source-code-plugin/{chainShortName}@truffle, you can find the {chainShortName} of different chains
here
, and set the explorerUrl to https://www.oklink.com.