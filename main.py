import base64
import os
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# --- 設定區 ---
# 優先讀取 Render 環境變數 GEMINI_API_KEY，如果沒有則使用後面括號內的預設 Key
GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY", "這裡貼上你的_GEMINI_API_KEY"
)

PROMPT_TEXT = """
你是一位頂級化學實驗室安全專家與 AI 視覺監控系統。
請仔細分析這張實驗室畫面，針對以下狀況進行綜合診斷：
1. 火焰/異常高溫（酒精燈失控、劇烈燃燒反應）。
2. 溶液狀態（溶液融合反應、劇烈顏色變化、突沸、試管/燒杯翻倒或液體潑灑）。
3. 氣體與煙霧（異常發煙、有毒氣體外洩）。
4. 設備與環境（儀器破損、防護裝備配戴狀況）。

【請嚴格依據以下結構回答】
1. **現狀診斷 (發生了什麼事)**：詳細描述畫面中的設備、液體狀態、氣體煙霧或翻倒狀況。
2. **危險等級與風險分析**：標示危險等級（低/中/高/極高），並說明潛在危害。
3. **標準處置 SOP (該如何正確處理)**：提供具體、條列式的緊急處置步驟。

如果畫面完全正常，請說明「目前實驗狀態穩定」，並給出常規安全提醒。
"""

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
# --------------

app = FastAPI(title="實驗室 全方位 AI 安全診斷系統")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🌟 關鍵新增：首頁路由 (當大家進入網址時，直接呈現 index.html 畫面)
@app.get("/", response_class=HTMLResponse)
async def get_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(
            "<h1>錯誤：找不到 index.html 檔案，請確認已上傳至根目錄</h1>",
            status_code=404,
        )


# 🌟 AI 診斷 API 路由
@app.post("/analyze")
async def analyze_lab_danger(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode("utf-8")

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": PROMPT_TEXT},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64_image,
                            }
                        },
                    ]
                }
            ]
        }

        response = requests.post(GEMINI_API_URL, json=payload, timeout=25)
        res_json = response.json()

        if response.status_code == 200:
            ai_reply = res_json["candidates"][0]["content"]["parts"][0]["text"]
            return {"status": "success", "analysis_result": ai_reply}
        else:
            print("【API 報錯詳情】:", res_json)
            error_msg = res_json.get("error", {}).get("message", "未知錯誤")
            return {
                "status": "error",
                "message": f"Google API 錯誤 ({response.status_code}): {error_msg}",
            }

    except Exception as e:
        return {"status": "error", "message": f"伺服器處理失敗: {str(e)}"}