const WebSocket = require('ws'); 
const fs = require('fs');
const axios = require('axios');
const { parse } = require('json2csv');

// WebSocket URLs
const xrpWebSocketURLs = ['wss://xrplcluster.com', 'wss://s1.ripple.com/', 'wss://s2.ripple.com/'];
const ethWebSocketURLs = [
    'https://api.noderpc.xyz/rpc-mainnet/public',
    'https://eth.nownodes.io/c4dcd45d-e2bd-4f3a-ab09-5ceacc4b5482',
    'https://mainnet.infura.io/v3/292f06c81c8c445ea092d9b3add9d517' // Replace with your actual Infura key
];

// Initialize data stores
let xrpData = [];
let ethData = [];

// Load accounts and signatures
const xrpAccounts = loadXrpAccounts('project.txt');
const { functionSignatures, eventSignatures } = loadSignatures('function.csv', 'event.csv');

// WebSocket Connection Handler
const connectWebSocket = (urls, type) => {
    urls.forEach(url => {
        const socket = new WebSocket(url);

        socket.on('open', () => {
            console.log(`Connected to ${type} WebSocket: ${url}`);
            const accounts = type === 'XRP' ? xrpAccounts : loadEthAccounts('C:\\Users\\LEGIONX\\Desktop\\blockchain_tools\\Ethereum_research\\wallets\\railgun.txt');
            if (type === 'XRP') {
                Object.keys(accounts).forEach(account => {
                    socket.send(JSON.stringify({ command: 'subscribe', accounts: [account] }));
                });
            } else {
                socket.send(JSON.stringify({ jsonrpc: '2.0', method: 'eth_newPendingTransactionFilter', id: 1 }));
                accounts.forEach(account => fetchLogsForAddress(account));
            }
        });

        socket.on('message', (message) => handleIncomingMessage(message, type));
        socket.on('error', (error) => console.error(`WebSocket error: ${error}`));
        socket.on('close', () => console.log(`Disconnected from ${type} WebSocket: ${url}`));
    });
};

// Handle incoming XRP messages
const handleIncomingMessage = (message, type) => {
    try {
        const parsedMessage = JSON.parse(message);
        if (type === 'XRP' && parsedMessage.result?.transactions) {
            parsedMessage.result.transactions.forEach(tx => {
                addXrpTransaction(tx);
            });
        } else if (type === 'ETH' && parsedMessage.method === 'eth_subscription') {
            processEthLog(parsedMessage.params.result);
        }
        updateDisplay(); // Update the HTML display after processing
    } catch (error) {
        console.error('Error parsing message:', error);
    }
};

// Add XRP transaction to data
const addXrpTransaction = (tx) => {
    if (!xrpData.find(item => item.transactionHash === tx.txid)) {
        xrpData.push({
            transactionHash: tx.txid,
            address: tx.Account,
            name: xrpAccounts[tx.Account] || 'Unknown',
            date: new Date(tx.date).toISOString(),
            blockNumber: tx.inLedger,
            timestamp: tx.date,
            transferType: tx.TransactionType,
            txnType: 'XRP',
            fromAddress: tx.Account,
            toAddress: tx.Destination,
            withdrawalValueETH: null,
            depositValueETH: null,
            withdrawalValueUSD: null,
            depositValueUSD: null,
            feeETH: tx.Fee / 1e6,
            feeUSD: null,
            topics: []
        });
    }
};

// Process Ethereum logs
const processEthLog = async (log) => {
    const tx = await getTransactionByHash(log.transactionHash);
    if (tx) {
        ethData.push({
            transactionHash: tx.hash,
            address: log.address,
            entity: log.entity, // Assuming entity and subentity is included in log
            subentity: log.subentity,
            date: new Date(tx.timestamp).toISOString(),
            blockNumber: tx.blockNumber,
            timestamp: tx.timestamp,
            transferType: log.input,
            txnType: 'ETH',
            fromAddress: tx.from,
            toAddress: tx.to,
            withdrawalValueETH: tx.value / 1e18,
            depositValueETH: null,
            withdrawalValueUSD: null,
            depositValueUSD: null,
            feeETH: (tx.gas * tx.gasPrice) / 1e18,
            feeUSD: null,
            topics: log.topics.map(topic => eventSignatures[topic] || topic),
        });
    }
};

// Load XRP accounts
function loadXrpAccounts(filePath) {
    const accounts = {};
    const fileContent = fs.readFileSync(filePath, 'utf-8').split('\n');
    fileContent.forEach(line => {
        const match = line.match(/(.*) - (.*) : (r[0-9A-Za-z]{25,34})/);
        if (match) {
            accounts[match[3].trim()] = match[1].trim();
        }
    });
    return accounts;
}

// Load signatures from CSV files
function loadSignatures(functionPath, eventPath) {
    const functionSignatures = fs.readFileSync(functionPath, 'utf-8').trim().split('\n').map(line => {
        const [signature, textSignature] = line.split(',');
        return { signature: signature.trim(), textSignature: textSignature?.trim() || '' };
    });

    const eventSignatures = fs.readFileSync(eventPath, 'utf-8').trim().split('\n').map(line => {
        const [signature, textSignature] = line.split(',');
        return { signature: signature.trim(), textSignature: textSignature?.trim() || '' };
    });

    return { functionSignatures, eventSignatures };
}

// Load Ethereum accounts
function loadEthAccounts(filePath) {
    const accounts = [];
    const fileContent = fs.readFileSync(filePath, 'utf-8').split('\n');
    fileContent.forEach(line => {
        const match = line.match(/(.*) - (.*) : (0x[a-fA-F0-9]{40})/);
        if (match) {
            accounts.push({
                entity: match[1].trim(),
                subentity: match[2].trim(),
                address: match[3].trim()
            });
        }
    });
    return accounts;
}

// Fetch logs for the given Ethereum address with retry logic
async function fetchLogsForAddress({ entity, subentity, address }) {
    const maxRetries = 5;
    let attempt = 0;

    while (attempt < maxRetries) {
        try {
            const logs = await getLogs(address);
            logs.forEach(log => {
                // Check for valid timestamp
                if (log.timestamp) {
                    const dateValue = new Date(log.timestamp);
                    if (!isNaN(dateValue.getTime())) { // Check if it's a valid date
                        ethData.push({
                            transactionHash: log.transactionHash,
                            address,
                            entity,
                            subentity,
                            date: dateValue.toISOString(),
                            blockNumber: log.blockNumber,
                            timestamp: log.timestamp,
                            transferType: log.input,
                            txnType: 'ETH',
                            fromAddress: log.from,
                            toAddress: log.to,
                            withdrawalValueETH: log.value / 1e18,
                            depositValueETH: null,
                            withdrawalValueUSD: null,
                            depositValueUSD: null,
                            feeETH: log.gas * log.gasPrice / 1e18,
                            feeUSD: null,
                            topics: log.topics.map(topic => eventSignatures[topic] || topic), // Convert topics to text_signature
                        });
                    } else {
                        console.error(`Invalid timestamp for log: ${JSON.stringify(log)}`);
                    }
                } else {
                    console.error(`Missing timestamp for log: ${JSON.stringify(log)}`);
                }
            });
            updateDisplay(); // Update the HTML display for Ethereum
            break; // Exit loop if successful
        } catch (error) {
            if (error.response && error.response.status === 429) {
                // If rate limit error, wait before retrying
                const waitTime = Math.pow(2, attempt) * 10000; // Exponential backoff
                console.log(`Rate limit reached. Waiting for ${waitTime / 8000} seconds...`);
                
                // Start spinner while waiting
                await spinWait(waitTime);
                
                attempt++;
            } else {
                console.error('Error fetching logs:', error);
                break; // Exit loop on other errors
            }
        }
    }
}

// Spinner function for interactive display
async function spinWait(waitTime) {
    const spinnerChars = ['|', '/', '-', '\\'];
    let index = 0;

    const spinnerInterval = setInterval(() => {
        // Clear the current line
        process.stdout.write(`\r${spinnerChars[index]}`);
        index = (index + 1) % spinnerChars.length;
    }, 100); // Adjust the speed of the spinner (100 ms per frame)

    // Wait for the specified wait time
    await new Promise(resolve => setTimeout(resolve, waitTime));
    
    clearInterval(spinnerInterval);
    process.stdout.write('\rDone!\n'); // Clear the spinner and show 'Done!'
}


// Fetch transaction by hash from Ethereum
async function getTransactionByHash(hash) {
    try {
        const response = await axios.post(ethWebSocketURLs[0], {
            jsonrpc: '2.0',
            method: 'eth_getTransactionByHash',
            params: [hash],
            id: 1
        });
        return response.data.result;
    } catch (error) {
        console.error('Error fetching transaction:', error);
    }
}

// Get logs for a specific address
async function getLogs(address) {
    const response = await axios.post(ethWebSocketURLs[0], {
        jsonrpc: '2.0',
        method: 'eth_getLogs',
        params: [{
            fromBlock: 'latest',
            toBlock: 'latest',
            address
        }],
        id: 1
    });
    return response.data.result;
}

// Update HTML display with transaction data
function updateDisplay() {
    const xrpTable = document.getElementById('xrp-table');
    const ethTable = document.getElementById('eth-table');

    // Clear previous data
    xrpTable.innerHTML = '';
    ethTable.innerHTML = '';

    // Populate XRP table
    xrpData.forEach(tx => {
        const row = xrpTable.insertRow();
        row.innerHTML = `
            <td>${tx.transactionHash}</td>
            <td>${tx.address}</td>
            <td>${tx.name}</td>
            <td>${tx.date}</td>
            <td>${tx.blockNumber}</td>
            <td>${tx.timestamp}</td>
            <td>${tx.transferType}</td>
            <td>${tx.txnType}</td>
            <td>${tx.fromAddress}</td>
            <td>${tx.toAddress}</td>
            <td>${tx.withdrawalValueETH}</td>
            <td>${tx.depositValueETH}</td>
            <td>${tx.withdrawalValueUSD}</td>
            <td>${tx.depositValueUSD}</td>
            <td>${tx.feeETH}</td>
            <td>${tx.feeUSD}</td>
        `;
    });

    // Populate Ethereum table
    ethData.forEach(tx => {
        const row = ethTable.insertRow();
        row.innerHTML = `
            <td>${tx.transactionHash}</td>
            <td>${tx.address}</td>
            <td>${tx.entity}</td>
            <td>${tx.subentity}</td>
            <td>${tx.date}</td>
            <td>${tx.blockNumber}</td>
            <td>${tx.timestamp}</td>
            <td>${tx.transferType}</td>
            <td>${tx.txnType}</td>
            <td>${tx.fromAddress}</td>
            <td>${tx.toAddress}</td>
            <td>${tx.withdrawalValueETH}</td>
            <td>${tx.depositValueETH}</td>
            <td>${tx.withdrawalValueUSD}</td>
            <td>${tx.depositValueUSD}</td>
            <td>${tx.feeETH}</td>
            <td>${tx.feeUSD}</td>
        `;
    });
}

// Connect to both XRP and Ethereum WebSocket nodes
connectWebSocket(xrpWebSocketURLs, 'XRP');
connectWebSocket(ethWebSocketURLs, 'ETH');

