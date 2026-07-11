import re

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Define Pydantic Model
pydantic_model = """
class AnalyzeInputRequest(BaseModel):
    input: str
"""
if "AnalyzeInputRequest" not in content:
    content = content.replace("class TraceRequest(BaseModel):", pydantic_model + "\nclass TraceRequest(BaseModel):")

# Define Endpoint
endpoint_code = """
@app.post("/api/tracer/analyze-input")
async def analyze_input(req: AnalyzeInputRequest):
    try:
        from services.transaction_analyzer import TransactionAnalyzer
        analyzer = TransactionAnalyzer()
        res = analyzer.analyze(req.input)
        return res
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/start_trace")
"""
if "/api/tracer/analyze-input" not in content:
    content = content.replace("@app.post(\"/api/start_trace\")", endpoint_code)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Injected /api/tracer/analyze-input into main.py successfully!")
