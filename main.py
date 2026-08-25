import io
import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from google import genai
from PIL import Image

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

app = FastAPI(title="實驗室 全方位 AI 安全診斷系統")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def get_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            "<h1>錯誤：找不到 index.html 檔案</h1>", status_code=404
        )


@app.post("/analyze")
async def analyze_lab_danger(file: UploadFile = File(...)):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, detail="Render 環境變數未設定 GEMINI_API_KEY"
        )

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="未接收到圖片檔案")

        # 圖片壓縮，加速 AI 運算
        image = Image.open(io.BytesIO(contents))
        image.thumbnail((1024, 1024))

        # 1. 初始化 Client
        client = genai.Client(api_key=api_key)

        # 2. 正確加上 models/ 前綴，符合最新 SDK 規範
        response = client.models.generate_content(
            model="models/gemini-3.6-flash", contents=[image, PROMPT_TEXT]
        )

        return {"status": "success", "analysis_result": response.text}

    except Exception as e:
        print("【API 呼叫失敗】:", str(e))
        return {"status": "error", "message": f"分析失敗: {str(e)}"}