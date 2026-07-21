import json
from urllib.parse import urlparse, parse_qs
from workers import WorkerEntrypoint, Response

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "OPTIONS":
            return Response("", headers=CORS_HEADERS)

        url = urlparse(request.url)
        params = parse_qs(url.query)
        method = request.method

        try:
            if url.path == "/health" and method == "GET":
                response = Response.json({
                    "status": "ok",
                    "version": "3.0.0-python",
                    "services": {
                        "d1": True,
                        "kv": True,
                        "r2": True
                    }
                })
                response.headers.update(CORS_HEADERS)
                return response
            
            # API Mock endpoints for now, the unified intelligence will auto-heal and expand these
            elif url.path == "/api/address" and method == "GET":
                address = params.get("address", [""])[0]
                chain = params.get("chain", ["ethereum"])[0]
                response = Response.json({
                    "address": address,
                    "chain": chain,
                    "balance": 0,
                    "transactions": []
                })
                response.headers.update(CORS_HEADERS)
                return response
                
            elif url.path == "/api/trace" and method == "POST":
                import js
                
                # Extract payload if possible
                try:
                    body = await request.json()
                except:
                    body = {}
                
                # Proxy to Compute Kernel (Layer 2)
                kernel_url = "http://127.0.0.1:8000/api/internal/job"
                payload = {
                    "action": "start_trace",
                    "address": body.get("address", ""),
                    "network": body.get("network", "ALL"),
                    "targetLoss": body.get("targetLoss", 0.0)
                }
                
                try:
                    from pyodide.ffi import to_js
                    # Use Pyodide FFI to call native JS fetch
                    opts_dict = {
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": json.dumps(payload)
                    }
                    from pyodide.ffi import to_js
                    import js
                    # dict_converter configures to_js to convert Python dicts to JS objects
                    opts = to_js(opts_dict, dict_converter=js.Object.fromEntries)
                    
                    res = await js.fetch(kernel_url, opts)
                    if res.ok:
                        kernel_resp = await res.json()
                        response = Response.json({
                            "traceId": "hybrid-trace-" + body.get("address", "")[:6],
                            "status": "processing",
                            "message": "Trace dispatched to Omni-Core Compute Kernel",
                            "kernel_response": kernel_resp.to_py()
                        })
                    else:
                        response = Response.json({
                            "traceId": "hybrid-trace-" + body.get("address", "")[:6],
                            "status": "failed",
                            "message": f"Kernel returned status {res.status}"
                        })
                except Exception as e:
                    response = Response.json({
                        "traceId": "hybrid-trace-" + body.get("address", "")[:6],
                        "status": "error",
                        "message": "Failed to reach Compute Kernel",
                        "detail": str(e)
                    })
                    
                response.headers.update(CORS_HEADERS)
                return response
                
            elif url.path == "/api/stats" and method == "GET":
                response = Response.json({
                    "addresses": 1337,
                    "transactions": 42000,
                    "traces": 99,
                    "labels": 500
                })
                response.headers.update(CORS_HEADERS)
                return response
                
            elif url.path == "/api/providers" and method == "GET":
                response = Response.json({
                    "providers": [{"chain": "ethereum", "provider": "etherscan", "hasKey": True}],
                    "total": 1
                })
                response.headers.update(CORS_HEADERS)
                return response
            
            # Catch all APIs
            elif url.path.startswith("/api/"):
                response = Response.json({"error": "not found", "path": url.path}, status=404)
                response.headers.update(CORS_HEADERS)
                return response

        except Exception as e:
            return Response.json(
                {"error": "Internal server error", "detail": str(e)},
                status=500,
                headers=CORS_HEADERS
            )

        # Fallback for unexpected routes
        return Response.json({"error": "Not found"}, status=404, headers=CORS_HEADERS)

    async def scheduled(self, controller, env, ctx):
        print("cron processed")

    async def queue(self, batch):
        for message in batch.messages:
            body = message.body
            message.ack()
