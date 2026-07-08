"""Background worker for processing pending VTON tasks.

Runs on Cloudflare Workers cron trigger (every 1 minute).
Polls YouCam API for tasks with status "processing" and updates D1.
"""

import json
import re
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
            status = result.get("status", "processing")

            if status == "completed":
                output_url = result.get("output_url", "")
                # Save to R2 for persistent storage (prevents broken images from expired freeimage.host URLs)
                from services.r2 import save_vton_output_to_r2
                r2_url = await save_vton_output_to_r2(env, task.user_id, task.id, output_url)
                await db.update_vton_result(task.id, {
                    "status": "completed",
                    "output_image_url": r2_url,
                    "completed_at": datetime.utcnow().isoformat(),
                })
                processed += 1

            elif status == "failed":
                await db.update_vton_result(task.id, {
                    "status": "failed",
                    "error_message": result.get("error", "YouCam task failed"),
                    "completed_at": datetime.utcnow().isoformat(),
                })
                processed += 1
                print(json.dumps({
                    "event": "vton_task_failed",
                    "task_id": task.id,
                    "youcam_task_id": task.youcam_task_id,
                    "error": result.get("error"),
                }))

        except Exception as e:
            print(json.dumps({
                "event": "vton_poll_error",
                "task_id": task.id,
                "youcam_task_id": task.youcam_task_id,
                "error": str(e),
            }))

    return {"processed": processed, "total_pending": len(pending_tasks)}


# Size suffixes to detect corrupted colors
_SIZE_SUFFIXES = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']


def _is_valid_color(color: str, product_name: str) -> bool:
    """Check if a color value is valid. Returns False if color is corrupted."""
    if not color:
        return False

    color_upper = color.upper().strip()

    # 1. Color contains product name -> invalid
    if product_name.lower() in color.lower():
        return False

    # 2. Color is a size (XS, S, M, L, XL, etc.) -> invalid
    for suffix in _SIZE_SUFFIXES:
        if color_upper == suffix or color_upper.endswith(f' {suffix}'):
            return False

    # 3. Color is a number (size) -> invalid
    if color_upper.isdigit():
        return False

    # 4. Color contains size-like patterns (e.g., "0-1M", "1-2M") -> invalid
    if re.match(r'^\d+-\d+M$', color_upper):
        return False

    return True


async def cleanup_corrupted_data(env):
    """Clean up products with corrupted colors (colors that are actually sizes).
    
    Capped at 20 pages (2000 products) per cron cycle to prevent timeouts.
    """
    db = DatabaseService(env)

    # Get all products (paginated) — capped to avoid consuming entire cron budget
    page = 1
    max_pages = 20
    total_fixed = 0
    total_checked = 0

    while page <= max_pages:
        products, total = await db.get_products({}, page=page, limit=100)
        if not products:
            break

        for product in products:
            total_checked += 1
            needs_update = False
            clean_colors = []

            for color in product.colors:
                if _is_valid_color(color, product.name):
                    clean_colors.append(color)
                else:
                    needs_update = True

            if needs_update:
                try:
                    await db.update_product_sizes(product.id, product.sizes, clean_colors)
                    total_fixed += 1
                    print(json.dumps({
                        "event": "cleanup_fixed",
                        "product_id": product.id,
                        "product_name": product.name,
                        "old_colors": product.colors,
                        "new_colors": clean_colors,
                    }))
                except Exception as e:
                    print(json.dumps({
                        "event": "cleanup_error",
                        "product_id": product.id,
                        "error": str(e),
                    }))

        # Next page
        if page * 100 >= total:
            break
        page += 1

    if total_fixed > 0:
        print(json.dumps({
            "event": "cleanup_complete",
            "checked": total_checked,
            "fixed": total_fixed,
        }))

    return {"checked": total_checked, "fixed": total_fixed}
