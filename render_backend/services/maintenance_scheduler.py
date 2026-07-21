import asyncio
import os
import subprocess
import datetime
import uuid
import logging
# Removed missing config import

logger = logging.getLogger("OmniChainEngine.Maintenance")

async def run_maintenance_task(mongo_db):
    logger.info("Starting Godmode Auto-Pilot Maintenance Task...")
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    report_id = f"MAINT-{uuid.uuid4().hex[:8].upper()}"
    
    # 1. Run the test script as a subprocess
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "test_full_system.py")
    
    try:
        process = await asyncio.create_subprocess_exec(
            "python", script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        raw_logs = stdout.decode() + "\n" + stderr.decode()
        status_flag = "FAIL" if "❌ FAIL" in raw_logs else "PASS"
    except Exception as e:
        raw_logs = f"Maintenance task failed to execute sub-process: {str(e)}"
        status_flag = "FAIL"
        
    logger.info(f"Maintenance execution complete. Status: {status_flag}. Ingesting logs into Godmode ML...")
    
    # 2. Feed to Godmode ML for insights
    ai_analysis = "No AI analysis could be generated (API key missing or failed)."
    gemini_keys = os.environ.get("GEMINI_API_KEYS", "") or os.environ.get("GEMINI_API_KEY", "")
    if gemini_keys:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_keys.split(",")[0].strip())
            prompt = f"""You are the Godmode Auto-Pilot Senior DevOps AI for the NEMESIS Intelligence Suite.
            Analyze these automated test suite logs and provide an executive summary of the system health.
            Include 3 sections:
            1. 📊 Health Summary
            2. 🛠️ Suggestions & Bug Fixes (if any FAIL states occurred, tell me exactly how to fix them)
            3. 🚀 Enhancements & Upgrades (suggest performance/security upgrades)
            
            Logs:
            {raw_logs[:8000]}  # Trim to avoid context limit
            """
            
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            ai_analysis = resp.text
        except Exception as e:
            logger.error(f"Godmode ML analysis failed: {e}")
            ai_analysis = f"AI analysis failed: {str(e)}"
            
    # 3. Persist to Database
    report = {
        "report_id": report_id,
        "timestamp": timestamp,
        "status": status_flag,
        "raw_logs": raw_logs,
        "ai_analysis": ai_analysis
    }
    
    if mongo_db is not None:
        try:
            await mongo_db.maintenance_reports.insert_one(report)
            logger.info(f"Maintenance report {report_id} persisted to database.")
        except Exception as e:
            logger.error(f"Failed to save maintenance report to DB: {e}")
            
    return report

async def weekly_maintenance_loop(mongo_db):
    """Background task that runs the maintenance suite once every 7 days."""
    while True:
        # Sleep 7 days (604800 seconds)
        await asyncio.sleep(604800)
        try:
            await run_maintenance_task(mongo_db)
        except Exception as e:
            logger.error(f"Weekly maintenance loop crashed: {e}")
