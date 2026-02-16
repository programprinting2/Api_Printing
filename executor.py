from tasks.merge_pdf import run as merge_pdf_run
from tasks.infojpeg import run as read_info_run
from tasks.infopdf import run as read_pdf_info_run

TASK_MAP = {
    "merge_pdf": merge_pdf_run,
    "read_info": read_info_run,
    "read_pdf_info": read_pdf_info_run
}

def execute(task_name, data):
    task = TASK_MAP.get(task_name)

    if not task:
        return {"status": "error", "message": "Task not found"}

    return task(data)
