// WEB3 & ETHERS.JS INTEGRATION
let provider = null;
let signer = null;
let connectedAddress = null;

async function connectWeb3Wallet() {
    if (window.ethereum == null) {
        alert("MetaMask or Web3 wallet not detected. Please install a Web3 provider.");
        return;
    }
    try {
        // Initialize ethers provider
        provider = new ethers.BrowserProvider(window.ethereum);
        signer = await provider.getSigner();
        connectedAddress = await signer.getAddress();
        
        // Update UI
        const btn = document.getElementById("web3-connect-btn");
        btn.innerHTML = `<i class="fa-solid fa-check-circle"></i> ${connectedAddress.substring(0, 6)}...${connectedAddress.substring(connectedAddress.length - 4)}`;
        btn.classList.replace("bg-indigo-600", "bg-emerald-600");
        btn.classList.replace("hover:bg-indigo-700", "hover:bg-emerald-700");
        btn.classList.replace("border-indigo-500", "border-emerald-500");
        
        // Set the connected address as the target
        document.getElementById("target-address").value = connectedAddress;
        
        // Optional: Fetch balance directly from blockchain via ethers.js
        const balanceWei = await provider.getBalance(connectedAddress);
        const balanceEth = ethers.formatEther(balanceWei);
        console.log(`[Web3] Direct On-Chain Balance: ${balanceEth} ETH`);
        
    } catch (error) {
        console.error("Web3 Connection Error:", error);
        alert("Failed to connect Web3 Wallet.");
    }
}

// TAB LOGIC
function switchTab(tabId, btnElement) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    btnElement.classList.add('active');
}

async function generateProfile() {
    const addr = document.getElementById('target-address').value.trim();
    if (!addr) { alert("Please enter an address"); return; }
    
    const loader = document.getElementById('ajax-loader');
    const dashboard = document.getElementById('dashboard-container');
    const loaderText = document.getElementById('loader-text');
    
    loader.style.display = 'flex';
    dashboard.classList.remove('hidden');
    
    // Use relative path for all API calls
    const baseUrl = '';

    try {
        // 1. Fetch Profile
        loaderText.innerText = "FETCHING WALLET PROFILE...";
        const profRes = await fetch(`${baseUrl}/api/nemesis_id/profile/${addr}`);
        if (profRes.ok) {
            const data = await profRes.json();
            document.getElementById('prof-address').innerText = data.address || addr;
            document.getElementById('prof-network').innerText = data.network || 'Unknown';
            document.getElementById('prof-entity').innerText = data.entity || 'Unknown / Unlabeled';
            document.getElementById('prof-balance').innerText = data.balance || '0.00';
            document.getElementById('prof-first').innerText = data.first_activity || 'N/A';
            document.getElementById('prof-last').innerText = data.last_activity || 'N/A';
            document.getElementById('prof-sent').innerText = data.total_sent || '0.00';
            document.getElementById('prof-received').innerText = data.total_received || '0.00';
            document.getElementById('prof-txcount').innerText = data.total_transactions || '0';
            
            const clusters = document.getElementById('prof-clusters');
            clusters.innerHTML = '';
            if (data.clustered_addresses && data.clustered_addresses.length) {
                data.clustered_addresses.forEach(c => {
                    clusters.innerHTML += `<li>${c}</li>`;
                });
            } else {
                clusters.innerHTML = '<li class="text-slate-400">No clusters detected</li>';
            }
        }

        // 2. Fetch AML
        loaderText.innerText = "CALCULATING AML RISK...";
        const amlRes = await fetch(`${baseUrl}/api/nemesis_id/aml/${addr}`);
        if (amlRes.ok) {
            const aml = await amlRes.json();
            const score = aml.score || 0; // 0 to 100
            const amlEl = document.getElementById('aml-score');
            amlEl.innerText = `${score}/100`;
            
            const bar = document.getElementById('aml-bar');
            bar.style.width = `${score}%`;
            if(score < 30) { bar.className = "h-full transition-all duration-1000 bg-emerald-500"; amlEl.className = "text-4xl font-black text-emerald-600"; }
            else if(score < 70) { bar.className = "h-full transition-all duration-1000 bg-amber-500"; amlEl.className = "text-4xl font-black text-amber-600"; }
            else { bar.className = "h-full transition-all duration-1000 bg-red-600"; amlEl.className = "text-4xl font-black text-red-600"; }
            
            document.getElementById('aml-exposure').innerText = `Exposure Rate: ${aml.exposure_rate || '0%'}`;
            
            const recEl = document.getElementById('aml-receivers');
            recEl.innerHTML = '';
            (aml.receivers || []).forEach(r => {
                recEl.innerHTML += `<li class="grid grid-cols-3 border-b border-slate-100 py-1"><span class="truncate pr-2">${r.wallet}</span><span>${r.count}</span><span>${r.amount}</span></li>`;
            });

            const senEl = document.getElementById('aml-senders');
            senEl.innerHTML = '';
            (aml.senders || []).forEach(s => {
                senEl.innerHTML += `<li class="grid grid-cols-3 border-b border-slate-100 py-1"><span class="truncate pr-2">${s.wallet}</span><span>${s.count}</span><span>${s.amount}</span></li>`;
            });
        }

        // 3. Fetch Intelligence
        loaderText.innerText = "QUERYING DARKNET & OSINT...";
        const intelRes = await fetch(`${baseUrl}/api/nemesis_id/intel/${addr}`);
        if (intelRes.ok) {
            const intel = await intelRes.json();
            
            const topEl = document.getElementById('intel-top');
            topEl.innerHTML = '';
            (intel.top_interacted || []).forEach(w => {
                topEl.innerHTML += `<li class="truncate py-1 border-b border-slate-100">${w}</li>`;
            });
            
            document.getElementById('intel-custodial').innerText = intel.custodial_entry || 'No known custodial entry points detected.';
            
            const malEl = document.getElementById('intel-malicious');
            malEl.innerText = intel.is_malicious ? 'YES' : 'NO';
            malEl.className = intel.is_malicious ? 'font-bold text-lg text-red-600' : 'font-bold text-lg text-emerald-600';
            
            document.getElementById('intel-social').innerText = intel.social_media || 'None';
            document.getElementById('intel-darknet').innerText = intel.darknet_mentions || '0 Mentions';
        }

        // 4. Fetch Tx History
        loaderText.innerText = "RETRIEVING TX HISTORY...";
        const txRes = await fetch(`${baseUrl}/api/nemesis_id/tx_history/${addr}`);
        if (txRes.ok) {
            const txs = await txRes.json();
            const tb = document.getElementById('tx-tbody');
            tb.innerHTML = '';
            (txs.transactions || []).forEach(tx => {
                let typeColor = tx.type.toLowerCase().includes('receive') ? 'text-emerald-600' : 'text-rose-600';
                tb.innerHTML += `
                    <tr class="hover:bg-slate-50">
                        <td class="px-4 py-2 font-bold ${typeColor}">${tx.type}</td>
                        <td class="px-4 py-2">${tx.timestamp}</td>
                        <td class="px-4 py-2 text-blue-600 truncate max-w-[100px]">${tx.hash}</td>
                        <td class="px-4 py-2 truncate max-w-[120px]">${tx.sender}</td>
                        <td class="px-4 py-2 truncate max-w-[120px]">${tx.receiver}</td>
                        <td class="px-4 py-2 text-right font-bold">${tx.amount}</td>
                        <td class="px-4 py-2">${tx.network}</td>
                    </tr>
                `;
            });
        }

        // 5. Trigger LLM Insights 
        loaderText.innerText = "GENERATING AI INSIGHTS...";
        const aiRes = await fetch(`${baseUrl}/api/nemesis_id/generate_report`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ address: addr, type: 'insights' })
        });
        if (aiRes.ok) {
            const ai = await aiRes.json();
            document.getElementById('insights-content').innerHTML = marked.parse(ai.markdown || "No insights generated.");
        }

    } catch (e) {
        console.error(e);
        alert("Error connecting to backend API: " + e.message);
    } finally {
        loader.style.display = 'none';
    }
}

async function requestFullReport() {
    const addr = document.getElementById('target-address').value.trim();
    if (!addr) { alert("Please enter an address and generate profile first."); return; }
    
    const btn = document.getElementById('btn-gen-full');
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Generating...';
    btn.disabled = true;
    
    const baseUrl = '';

    try {
        const aiRes = await fetch(`${baseUrl}/api/nemesis_id/generate_report`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ address: addr, type: 'full' })
        });
        if (aiRes.ok) {
            const ai = await aiRes.json();
            document.getElementById('fullreport-content').innerHTML = marked.parse(ai.markdown || "Failed to generate.");
        }
    } catch (e) {
        alert("Failed to generate full report: " + e.message);
    } finally {
        btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generate Full Report';
        btn.disabled = false;
    }
}

async function exportToPDF(elementId, filename) {
    const element = document.getElementById(elementId);
    
    // Add a temporary class to ensure it's not hidden if rendering an inactive tab
    const originalDisplay = element.style.display;
    element.style.display = 'block';
    
    try {
        const canvas = await html2canvas(element, { scale: 2, useCORS: true });
        const imgData = canvas.toDataURL('image/png');
        const pdf = new jspdf.jsPDF('p', 'mm', 'a4');
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
        
        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
        pdf.save(`${filename}_${document.getElementById('target-address').value.substring(0,6)}.pdf`);
    } catch (e) {
        console.error(e);
        alert("Error exporting PDF: " + e.message);
    } finally {
        element.style.display = originalDisplay;
    }
}
