import io
import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from google import genai
from PIL import Image

PROMPT_TEXT = """
你是一位頂級化學與生物實驗室安全專家與 AI 視覺監控系統。
請針對這張實驗室畫面進行高精準度的專業安全診斷。

【重點檢測項目與實驗情境】
1. **加熱與熱源反應**：酒精燈/加熱板使用狀況、本生燈火焰失控、水浴/油浴溫度異常發煙。
2. **液體與化學品操作**：
   - 滴定/混合反應：劇烈顏色變化、突沸、異常冒泡。
   - 容器與儲存：燒杯/試管/錐形瓶翻倒、化學品潑灑、未標示之危害液體。
   - 溶劑危害：易燃有機溶劑（如乙醇、丙酮）是否過度靠近熱源。
3. **氣體與通風**：異常發煙、揮發性氣體外洩、是否需在「抽氣煙櫥 (Fume Hood)」內操作卻未執行。
4. **個人防護 (PPE) 與環境安全**：
   - 實驗人員是否配戴護目鏡、實驗衣、適當手套。
   - 桌面雜物過多、防護裝備破損、緊急洗眼器/滅火器通道被阻擋。

【請嚴格依據以下結構回答】
1. **🔍 識別實驗類型與現狀**：辨識畫面中正在進行的實驗或設備（如：酸鹼滴定、加熱迴流、溶液配製等）與當前狀態。
2. **⚠️ 危害等級與特定風險**：標示危險等級（低 / 中 / 高 / 極高），並指出該實驗最易引發的特有風險。
3. **🚨 針對性緊急處置 SOP**：給出 3 點極具針對性、條列式的緊急處置步驟。

若畫面完全正常，請回答「目前實驗狀態穩定，運算子合規範」，並給出該實驗項目的預防性提醒。
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