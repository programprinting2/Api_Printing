from tasks.merge_pdf import run as merge_pdf_run
from tasks.infojpeg import run as read_info_run
from tasks.infopdf import run as read_pdf_info_run
import concurrent.futures
import threading

TASK_MAP = {
    "merge_pdf": merge_pdf_run,
    "read_info": read_info_run,
    "read_pdf_info": read_pdf_info_run
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
        return {"status": "error", "message": f"Task timed out after {timeout_seconds}s"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
