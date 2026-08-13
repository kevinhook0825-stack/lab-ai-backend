import google.generativeai as genai

# 請填入你的 API Key
GEMINI_API_KEY = "AQ.Ab8RN6JTjMF3-pO7f85MuP2Fqk8q_kgxyuwh-TsZtKSR1RoIag"

genai.configure(api_key=GEMINI_API_KEY)

try:
    print("正在連接 Gemini API...")
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Hello! 請簡短回應：你是實驗室安全專家嗎？")
    print("【API 測試成功！】Gemini 回覆：")
    print(response.text)
except Exception as e:
    print("【API 測試失敗！】錯誤原因：")
    print(e)