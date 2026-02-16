import os
from PyPDF2 import PdfMerger

def run(data):
    file1 = data.get("file1")
    file2 = data.get("file2")
    output = data.get("output")

    if not file1 or not file2 or not output:
        return {"status": "error", "message": "Missing parameter"}

    try:
        merger = PdfMerger()
        merger.append(file1)
        merger.append(file2)
        merger.write(output)
        merger.close()

        return {
            "status": "success",
            "output": output
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
