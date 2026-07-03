import requests
import time
import json
import logging
from rich.console import Console

console = Console()
logging.basicConfig(level=logging.INFO, format='%(message)s')

API_URL = "http://localhost:3001/api/start_trace"

SCENARIOS = [
    {
        "name": "Iran-Linked / JASTA Cases (IRGC/Binance)",
        "network": "TRON / BTC",
        "loss": "$334,000,000 (Frozen USDT Assets); ~12,271 BTC; $177,101,659.84",
        "description": "State-sponsored laundering and terror financing involving IRGC, IQRG-QF, IFSR, Tether Ltd. (Custodian/Admin), Binance, Hamas, PIJ, LuBian pool, Fazenda Amazonia (Laundering Front), Iran and China Investment Development Group, Buy Cash, Dubai Co.",
        "seeds": [
            "TNiq9AXBp9EjUqhDhrwrfvAA8U3GUQZH81",
            "TTiDLWE6fZK8okMJv6ijg42yrH6W2pjSr9",
            "TRug7ZsKi7LjSg2n8A9a2CUFurE6u6HSwb",
            "TTTSEpcsZgqjgqVpwaLp2PZy41TGC1puCG",
            "TAUN6FwrnwwmaEqYcckffC7wYmbaS6cBiX",
            "TXBMWt3T4WhFkcPnob1567cGDM3ou27GWE",
            "TAssM3ZebjsscHBkL6T1WfvsDm2qdYagLJ",
            "364XjdP6Jbpm945DW4M6EobXLEmJv964rC",
            "3QLeXx1J9Tp3TBnQyHrhVxne9KqkAS9JSR",
            "32Df7gbuSG6g7caY3gxxxYabryv2eoD1n4",
            "3DEgB8cz63rNTcAYRatFSHhb1kUTwaoyRe",
            "3Pja5FPK1wFB9LkWWJai8XYL1qjbqqT9Ye",
            "3FrM1He2ZDbsSKmYpEZQNGjFTLMgCZZkaf",
            "34Jpa4Eu3ApoPVUKNTN2WeuXVVq1jzxgPi",
            "38Md7BghVmV7XUUT1Vt9CvVcc5ssMD6ojt",
            "3AWpzKtkHfWsiv9RGXKA3Z8951LefsUGXQ"
        ]
    },
    {
        "name": "Ray L.",
        "network": "EVM (Ethereum)",
        "loss": "$613,284.35",
        "description": "Crypto Investment Fraud linked to entities including Strcoin, Strcoinet, Imkey, DiaPro.",
        "seeds": [
            "0x94BD8569BaA5E0aDf70e1032c1F05EeA7f72707E",
            "0x3b5c0DCcd73448e6380202234d18aCDe04Eef2D6",
            "0x97A2097a7E28Ae0676C7CA1E4d3dEC24969E49c5"
        ]
    },
    {
        "name": "Rhonda Malnar",
        "network": "BTC / EVM",
        "loss": "$30,000 (First Scam); $6,500.00 (Recovery Scam Fees)",
        "description": "Multi-Scam. Initially defrauded by an 'elon musk scammer', followed by a secondary fraud from a 'Mitch Crypto' recovery scammer operating out of Australia.",
        "seeds": [
            "35caEbxuUYhnECA86fx9MKDA91h9SWTfEe",
            "bc1qsy8m94zqa6qhuv5afhyp057azuO2msmrtgdxpm",
            "3KKZjqr1qsjXwmkibGgGs7dCJyED4NX17P",
            "bc1qlkcvapmzdv5jatmzcgar9fwwwx7yg62mjuj2cke",
            "0x633304F1c8Fb790595A7F6972C1808b32029d29",
            "0x282aEc1797d062A5fbCc9fb325982543d10",
            "bc1qOtyqkufqe9hyylfexamekqa8fqsw33urg5pjmr"
        ]
    },
    {
        "name": "Bruce S.",
        "network": "BTC / NEAR",
        "loss": "$1,299,528.55 USD",
        "description": "Trezor Hack resulting in high-volume unauthorized transfers. Funds were moved through OKX-EXCHANGE, FIXEDFLOAT, and NEAR Deposits using opreturn.net.",
        "seeds": [
            "bc1qf8m36m57wal9u5wn7pqre586jvf3qqfn0dw54z",
            "bc1qyea5ak8385dpp953759ldcjlh2kd8c5yrumda5",
            "bc1ptwlknq9w7nxa4ejyu66nn8n4vejl64p2u8g9ars808850zkm06pqxtymw6",
            "bc1qjnp7qhwrhw3e7elpmlh7m5ec832nexx6vx7585",
            "3A6JgF1JfG7BANTYKizCs2jUCnWrEpd5A8",
            "bc1q6dmu9u2eh2as3fma3nfy0yzj9466wnjqlhjqmx0x4ff66d57482F616eAC22470d99703CEb667c48be"
        ]
    },
    {
        "name": "Joseph Novak",
        "network": "ETH",
        "loss": "$382,202.83 USD",
        "description": "Pig Butchering Scam. Defrauded by the 'Mekong-04' syndicate utilizing a synthetic persona ('Ailis Danner / Trotter'). Assets were pulled via a malicious DApp (defiai.top) and routed through Wintermute to Binance.",
        "seeds": [
            "0x4ff66d57482F616eAC22470d99703CEb667c48be"
        ]
    },
    {
        "name": "Lance Migliaccio",
        "network": "ETH / ERC-20",
        "loss": "$47,800–$50,000",
        "description": "DOT Miners Scam. Orchestrated by Arun Ravindranathan, Arun Saroj, Kehul Vikram Patel, DOT Miners, DOT HQ Limited, DOT Fintech Limited, etc.",
        "seeds": [
            "bc1qpa8n0a5ckt7wkdw3cn8eklsz3z0kn89knme5a9"
        ]
    },
    {
        "name": "Frank P",
        "network": "BTC",
        "loss": "1.6M",
        "description": "Pig Butchering - Romance Scam. Perpetrator used the alias 'Lin Chen.' Funds were moved via domestic wire transfers to CoinFlip, followed by international transfers with the final destination being an OKX exchange wallet.",
        "seeds": [
            "ra58paZqDhh2e6LtA4VPQEgAztUz3Z3urq"
        ]
    },
    {
        "name": "Unknown (Case ID: 202508-06)",
        "network": "XRP",
        "loss": "$1.04 million USD equivalent",
        "description": "Phishing Attack. The victim was convinced by threat actors impersonating Ledger wallet support to enter their seed phrase into a fake website.",
        "seeds": [
            "bc1qcrdrmxx49pfzrmltx6my4cp62n6t4e58jeu0y7"
        ]
    },
    {
        "name": "Unknown (Case ID: 202508-07)",
        "network": "BTC",
        "loss": "0.7 M USD",
        "description": "Stolen Funds (Fake Trading-Fake Recovery). Sender: Coinbase, Receiver: ChangeNow.",
        "seeds": [
            "0x159a861a3f0838adb1e6895886c7a0be7158be89"
        ]
    },
    {
        "name": "Randy J",
        "network": "ETH",
        "loss": "88.2381 ETH",
        "description": "Token Transfer incident (Multi-Chain).",
        "seeds": [
            "0x2042404183ecd9610da5b251bb5f6e93eb9d3e08"
        ]
    },
    {
        "name": "Jarryd L",
        "network": "ETH",
        "loss": "$50,000.00",
        "description": "Scam associated with the malicious website etherscanverify.eth.",
        "seeds": [
            "uThZSCB2R8UQXHuPKPQLrRC5n7VTdSqUrJDQuoJsNum",
            "6vMuna31vRDs9u9RAEF8UeCSs9CNu6j4LkXpe4Ko1gBQ",
            "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t",
            "J7RBLx4gr5QisTidhJEzMj4awHz2ajwWKVREwN2J2TKR"
        ]
    },
    {
        "name": "Unknown (Ethereum Scam - Case 202508-05)",
        "network": "ETH",
        "loss": "$44,000 - $45,000",
        "description": "Funds stolen from a Coinbase account were withdrawn to privately controlled wallets, obfuscated using Tokenlon DEX, and cashed out at Binance.",
        "seeds": [
            "0x60E760222474A10f378cD53A5Bcd2CBd5a70eD1F",
            "0x0ed649357AbdAaA0222fE452B50D61D3E4a263a8"
        ]
    },
    {
        "name": "Unknown (USDC Scam - Cases 202508-06 & 202508-07)",
        "network": "ETH",
        "loss": "$134,900.00",
        "description": "Scammers directed victim to interact with the USDC contract to swap stolen Ether for USDC. Funds were transferred through this contract to the scammer-controlled wallet.",
        "seeds": [
            "0x6f00b583914fb35d314b36d2d914c145210be24e",
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "0x53556d7f1553Fa43D446D5363426447c40EDeAb3"
        ]
    },
    {
        "name": "Unknown (TRX Online Friend Scam - Case 202508-08)",
        "network": "TRX",
        "loss": "306k USD",
        "description": "Victim was tricked by an online friend who provided a 'poisoned' QR code after asking for 25 USD in TRX, resulting in the theft of their entire Exodus wallet balance.",
        "seeds": [
            "TNcykrU6R99SrR5BnxaqtDZe1V7o2sf664",
            "TRvR28GtTsWTLqxih6QAzDSrTCUcSZ7BQ6",
            "TAYXXGnW4h93os61Y4CrB3Xh8NunYCfAzr",
            "TBQmanVxhpdBHw9wpW2i4wER5e7gyjv1zS",
            "TBbsm8SCvGrhxzv4zpa98DmszixP3hCpsK",
            "TNm4uUAWSDKVU6sPKEcATSKjs1bUCzEd3k",
            "TUTkCjL1DTPCdFStVzsAHRQnUJJZpbVo1s"
        ]
    },
    {
        "name": "Unknown (Binance Incident)",
        "network": "ETH",
        "loss": "$400k",
        "description": "Fraudulent transfer linked to BINANCE.",
        "seeds": [
            "0x13d2d1f8e62f1f57eab648076583d7ce9f2af867"
        ]
    },
    {
        "name": "Unknown (August 19 Incident)",
        "network": "ETH",
        "loss": "$340k",
        "description": "Investigation labeled 'In Process'.",
        "seeds": [
            "0x7CA30EEE61DD4E2356B2aE59718C23C3C470D3bB",
            "0xf006878B4232C3281C545ae205Eda784DA6EAEAA",
            "GCMPTBICKA5R4HN2DMRSNPMFWGYN5YO73R4B3DUD3SG7OZGCI4LRA3BP",
            "r9xM4fYBKM9EJcvECEgzcmwMjG5QQeJP8z",
            "bc1qphlqxrjgnj6aa0lnmv4kdgxyefk363sxwpp4tp",
            "0x041a583db93c1bfc883583d08fbc2bb001edd25a"
        ]
    }
]

def run_tests():
    console.print(f"\n[bold green]🚀 NEMESIS OMNI-TESTER INITIATED[/bold green]")
    console.print(f"[*] Loaded {len(SCENARIOS)} complex tracing scenarios.\n")
    
    report = []
    
    for i, case in enumerate(SCENARIOS):
        console.print(f"[bold cyan]--- SCENARIO {i+1}/{len(SCENARIOS)}: {case['name']} ---[/bold cyan]")
        console.print(f"Network: {case['network']} | Loss: {case['loss']}")
        console.print(f"Desc: {case['description']}\n")
        
        for address in case["seeds"]:
            console.print(f"[*] Tracing Seed: {address} ...")
            
            payload = {
                "seeds": address,
                "chain_override": "AUTO", 
                "max_depth": 1,
                "tracing_method": "tracer"
            }
            
            try:
                # Trigger trace on local backend
                response = requests.post(API_URL, json=payload, timeout=120)
                
                if response.status_code == 200:
                    data = response.json()
                    console.print(f"[bold green][+] Success![/bold green] Found {len(data.get('nodes', []))} nodes and {len(data.get('edges', []))} edges.")
                    report.append({
                        "case": case['name'],
                        "address": address,
                        "status": "Success",
                        "nodes_found": len(data.get('nodes', [])),
                        "edges_found": len(data.get('edges', []))
                    })
                else:
                    console.print(f"[bold red][!] HTTP Error {response.status_code}: {response.text}[/bold red]")
                    report.append({
                        "case": case['name'],
                        "address": address,
                        "status": f"Failed - HTTP {response.status_code}"
                    })
                    
            except requests.exceptions.ConnectionError:
                console.print("[bold red][!] Connection Refused. Is the FastAPI backend running on port 3001?[/bold red]")
                return
            except Exception as e:
                console.print(f"[bold red][!] Exception during trace: {e}[/bold red]")
                report.append({
                    "case": case['name'],
                    "address": address,
                    "status": f"Error - {str(e)}"
                })
                
            # Wait 5 seconds between requests to avoid rate limits
            console.print("[*] Sleeping for 5 seconds to prevent rate-limits...")
            time.sleep(5)
            
    # Write report
    with open("test_results_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
        
    console.print(f"\n[bold green]✅ TESTING COMPLETE. Report saved to 'test_results_report.json'[/bold green]")

if __name__ == "__main__":
    run_tests()
