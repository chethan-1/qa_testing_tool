from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import json
import requests
app = FastAPI(title="QA Tool")

@app.get("/health")
def health():
    return {"status": "ok"}


def get_value_from_json(data, path):
    """
        Simple json path like: data[0].id or id
        """
    try:
        for part in path.replace("]", "").split("."):
            if "[" in part:
                key, index = part.split("[")
                data = data[key][int(index)]
            else:
                data = data[part]
        return data
    except Exception:
        return None


@app.post("/run-tests")
async def run_tests(file: UploadFile = File(...)):

    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Only Excel files are allowed"
        )

    try:
        df = pd.read_excel(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    results = []

    for _, row in df.iterrows():
        test_name = row.get("test_name", "Unnamed Test")
        method = str(row.get("method", "GET")).upper()
        url = row.get("url")

        expected_status = int(row.get("expected_status", 200))
        json_path = str(row.get("json_path", "")).strip()
        expected_value = str(row.get("expected_value", "")).strip()

        try:
            headers = json.loads(row.get("headers", "{}"))
            body = json.loads(row.get("body", "{}"))
        except Exception:
            headers = {}
            body = {}

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                timeout=10
            )

            actual_status = response.status_code
            status_match = actual_status == expected_status

            json_match = True
            actual_value = None

            if json_path:
                response_json = response.json()
                actual_value = get_value_from_json(response_json, json_path)
                json_match = str(actual_value) == expected_value

            test_status = "PASS" if status_match and json_match else "FAIL"

        except Exception:
            test_status = "ERROR"
            actual_status = None
            actual_value = None

        results.append({
            "test_name": test_name,
            "status": test_status,
            "expected_status": expected_status,
            "actual_status": actual_status,
            "expected_value": expected_value,
            "actual_value": actual_value
        })
        print(response)

    return {
        "total_tests": len(results),
        "passed": len([r for r in results if r["status"] == "PASS"]),
        "failed": len([r for r in results if r["status"] != "PASS"]),
        "results": results
    }



# @app.post("/upload-excel")
# async def upload_excel(file: UploadFile = File(...)):
#     if not file.filename.endswith((".xlsx",".xls")):
#         raise HTTPException(status_code=400, detail="Only Excel Files are allowed")
#     try:
#         df = pd.read_excel(file.file)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Failed to read Excel: {str(e)}")
#
#     if df.empty:
#         raise HTTPException(status_code=400, detail="Excel file is empty")
#
#     data = df.fillna("").to_dict(orient="records")
#
#     return {
#         "filename": file.filename,
#         "total_tests": len(data),
#         "data": data
#     }