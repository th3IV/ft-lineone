"""Background worker for processing pending VTON tasks.

Runs on Cloudflare Workers cron trigger (every 1 minute).
Polls YouCam API for tasks with status "processing" and updates D1.
"""

import json
from datetime import datetime
from services.database import DatabaseService
from services.youcam import YouCamService


async def process_pending_vton_tasks(env):
    """Poll YouCam for pending VTON tasks and update D1."""
    db = DatabaseService(env)
    youcam = YouCamService(env=env)

    pending_tasks = await db.get_pending_vton_tasks(limit=10)

    if not pending_tasks:
        return {"processed": 0}

    processed = 0
    for task in pending_tasks:
        try:
            result = await youcam.poll_task(task.youcam_task_id)

            if result["status"] == "completed":
                await db.update_vton_result(task.id, {
                    "status": "completed",
                    "output_image_url": result.get("output_url"),
                    "completed_at": datetime.utcnow().isoformat(),
                })
                processed += 1

            elif result["status"] == "failed":
                await db.update_vton_result(task.id, {
                    "status": "failed",
                    "error_message": result.get("error", "YouCam task failed"),
                    "completed_at": datetime.utcnow().isoformat(),
                })
                processed += 1

        except Exception as e:
            print(json.dumps({
                "event": "vton_poll_error",
                "task_id": task.id,
                "youcam_task_id": task.youcam_task_id,
                "error": str(e),
            }))

    return {"processed": processed, "total_pending": len(pending_tasks)}
