import streamlit as st
import google.generativeai as genai

# 設定頁面
st.set_page_config(page_title="AI 智能減重助手", page_icon="🥗")

# 1. 側邊欄設定
st.sidebar.header("⚙️ 個人身體數據")
gender = st.sidebar.radio("生理性別", ["男", "女"])
age = st.sidebar.number_input("年齡", 10, 100, 30)
height = st.sidebar.number_input("身高 (cm)", 100, 250, 170)
weight = st.sidebar.number_input("體重 (kg)", 30, 200, 70)
activity = st.sidebar.selectbox("活動量", ["久坐", "輕度", "中度", "高度", "超高度"])
garmin = st.sidebar.number_input("Garmin 今日消耗 (kcal)", 0, 5000, 0)

# 2. 計算 TDEE
def calc_tdee(gender, w, h, a, act):
    bmr = (10*w + 6.25*h - 5*a + 5) if gender == "男" else (10*w + 6.25*h - 5*a - 161)
    multipliers = {"久坐":1.2, "輕度":1.375, "中度":1.55, "高度":1.725, "超高度":1.9}
    return int(bmr * multipliers[act])

tdee = calc_tdee(gender, weight, height, age, activity)
limit = tdee + garmin - 500 # 減重目標

# 3. 主畫面
st.title("🥗 AI 智能減重助手")
col1, col2 = st.columns(2)
col1.metric("基礎代謝 TDEE", f"{tdee} kcal")
col2.metric("今日建議攝取", f"{limit} kcal")

# 4. API 設定與影像分析
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("尚未設定 API Key")
    st.stop()

uploaded_file = st.file_uploader("📸 上傳食物照片", type=["jpg", "png", "jpeg"])
if uploaded_file and st.button("🔍 開始分析"):
    with st.spinner("AI 正在分析..."):
        try:
            # 使用最新的 Flash 模型
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"你是營養師。請分析這張圖的食物，列出：1.食物名稱 2.估算熱量 3.營養素(蛋白/脂肪/碳水)。最後給出簡短建議，使用者的今日剩餘額度是 {limit} kcal。"
            
            # 處理圖片
            img_data = [{"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}]
            
            response = model.generate_content([prompt, img_data[0]])
            st.markdown(response.text)
        except Exception as e:
            st.error(f"錯誤：{e}")
