import os
import re

def patch():
    src = "templates/index.html"
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "async function initiateLandingTrace()" not in content:
        func = """
            async function initiateLandingTrace() {
                const seedVal = document.getElementById("landing-seed-input") ? document.getElementById("landing-seed-input").value : null;
                const amtVal = document.getElementById("landing-target-amount") ? document.getElementById("landing-target-amount").value : null;
                
                if(!seedVal) return alert("Please enter a target wallet address.");
                
                // Hide landing, show UI
                let lp = document.getElementById('landing-page');
                let mu = document.getElementById('main-ui');
                if(lp) lp.classList.add('hidden');
                if(mu) {
                    mu.classList.remove('hidden');
                    mu.classList.add('flex');
                }
                
                // Set the value in the main UI input
                let mainInput = document.getElementById("seed-input");
                if (mainInput) mainInput.value = seedVal;
                let mainAmt = document.getElementById("target-amount");
                if (mainAmt && amtVal) mainAmt.value = amtVal;
                
                // Call submitTrace
                submitTrace();
            }

            async function fetchHistoricalTrace() {
                const searchVal = document.getElementById("landing-search-trace") ? document.getElementById("landing-search-trace").value : null;
                if(!searchVal) return alert("Please enter a Nemesis ID or Trace ID.");
                
                // Set main search bar and call its search
                let lp = document.getElementById('landing-page');
                let mu = document.getElementById('main-ui');
                if(lp) lp.classList.add('hidden');
                if(mu) {
                    mu.classList.remove('hidden');
                    mu.classList.add('flex');
                }
                
                let searchInput = document.getElementById("search-node-input");
                if (searchInput) searchInput.value = searchVal;
                
                // Simulate trace retrieval
                alert("Retrieving Historical Trace: " + searchVal);
            }
"""
        content = content.replace("async function submitTrace() {", func + "\n            async function submitTrace() {")
        with open(src, "w", encoding="utf-8") as f:
            f.write(content)
        print("Patched index.html")

if __name__ == "__main__":
    patch()
