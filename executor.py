from tasks.merge_pdf import run as merge_pdf_run
from tasks.compose_pdf_sheet import run as compose_pdf_sheet_run
from tasks.infojpeg import run as read_info_run
from tasks.infopdf import run as read_pdf_info_run
from tasks.image_processing import process_image
from tasks.render_cmyk import render_cmyk
from tasks.cmyk_master import export_cmyk_master
from tasks.export_pdf_imposition import export_pdf_imposition
from tasks.spot_color import run as spot_color_run
from tasks.finishing_editor import run as finishing_editor_run
import concurrent.futures
import threading

TASK_MAP = {
    "merge_pdf": merge_pdf_run,
    "compose_pdf_sheet": compose_pdf_sheet_run,
    "read_info": read_info_run,
    "read_pdf_info": read_pdf_info_run,
    "image_processing": process_image,
    "render_cmyk": render_cmyk,
    "export_cmyk_master": export_cmyk_master,
    "export_pdf_imposition": export_pdf_imposition,
    "spot_color": spot_color_run,
    "finishing_process": finishing_editor_run,
}

# Shared thread pool for running tasks asynchronously with a timeout
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def execute(task_name, data, timeout_seconds=30):
    task = TASK_MAP.get(task_name)
    if not task:
        return {"status": "error", "message": "Task not found"}

    future = _executor.submit(task, data)
    try:
        result = future.result(timeout=timeout_seconds)
        return result
    except concurrent.futures.TimeoutError:
        # Attempt to cancel (may not stop if task is non-interruptible)
        future.cancel()
        return {
            "status": "error",
            "message": f"Task timed out after {timeout_seconds}s",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
