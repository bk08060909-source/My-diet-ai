import streamlit as st
import google.generativeai as genai

# 設定頁面標題與圖示
st.set_page_config(page_title="AI 智能減重助手", page_icon="🥗")

# 側邊欄：使用者設定
st.sidebar.header("⚙️ 個人身體數據")
st.sidebar.info("請輸入你的身體數值以計算 TDEE")

gender = st.sidebar.radio("生理性別", ["男", "女"])
age = st.sidebar.number_input("年齡", min_value=10, max_value=100, value=30)
height = st.sidebar.number_input("身高 (cm)", min_value=100, max_value=250, value=170)
weight = st.sidebar.number_input("體重 (kg)", min_value=30, max_value=200, value=70)
activity_level = st.sidebar.selectbox(
    "日常活動量",
    ("久坐 (辦公室工作)", "輕度活動 (每週運動1-3天)", "中度活動 (每週運動3-5天)", "高度活動 (每週運動6-7天)", "超高度活動 (勞力工作/運動員)")
)
garmin_calories = st.sidebar.number_input("Garmin 今日消耗 (kcal)", min_value=0, value=0, help="請查看手錶上的'主動消耗'熱量")

# BMR & TDEE 計算 (Mifflin-St Jeor 公式)
def calculate_metrics(gender, weight, height, age, activity_level):
    if gender == "男":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    
    activity_multipliers = {
        "久坐 (辦公室工作)": 1.2,
        "輕度活動 (每週運動1-3天)": 1.375,
        "中度活動 (每週運動3-5天)": 1.55,
        "高度活動 (每週運動6-7天)": 1.725,
        "超高度活動 (勞力工作/運動員)": 1.9
    }
    tdee = bmr * activity_multipliers[activity_level]
    return int(tdee)

base_tdee = calculate_metrics(gender, weight, height, age, activity_level)
total_daily_limit = base_tdee + garmin_calories # 加上運動消耗
target_deficit = 500 # 預設減重赤字
suggested_intake = total_daily_limit - target_deficit

# 主畫面
st.title("🥗 AI 智能減重助手")
st.write("拍照上傳，立刻分析熱量與營養素！")

# 顯示數據儀表板
col1, col2, col3 = st.columns(3)
col1.metric("基礎 TDEE", f"{base_tdee} kcal")
col2.metric("Garmin 補償", f"+{garmin_calories} kcal")
col3.metric("今日建議攝取", f"{suggested_intake} kcal", delta=f"-{target_deficit} 減重目標")

st.markdown("---")

# 處理 API Key (從 Streamlit Secrets 讀取)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("尚未設定 API Key，請至 Streamlit Cloud 設定 Secrets。")
    st.stop()

# 圖片上傳區
uploaded_file = st.file_uploader("📸 拍攝或上傳食物照片", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 顯示圖片
    st.image(uploaded_file, caption="你的食物", use_container_width=True)
    
    if st.button("🔍 開始 AI 分析"):
        with st.spinner("AI 正在觀察你的食物...請稍候"):
            try:
                # 準備 Prompt
                model = genai.GenerativeModel('gemini-1.5-pro')
                # 這裡就是你的「系統指令」
                input_prompt = f"""
                你是一位專業營養師。請分析這張圖片中的食物：
                1. 辨識所有食物項目。
                2. 估算各項目的份量與熱量。
                3. 總結這餐的總熱量、蛋白質、脂肪、碳水化合物。
                4. 使用者的今日建議攝取量是 {suggested_intake} kcal。
                請根據這個建議量，給出簡短的點評（例如：這餐是否太油？是否還有額度吃晚餐？）。
                
                請用繁體中文回答，並使用 Markdown 表格呈現數據。
                """
                
                # 處理圖片格式以符合 API 要求
                image_data = [{"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}]
                
                # 發送請求
                response = model.generate_content([input_prompt, image_data[0]])
                
                # 顯示結果
                st.markdown("### 📊 分析報告")
                st.markdown(response.text)
                st.success("分析完成！")
                
            except Exception as e:
                st.error(f"發生錯誤：{str(e)}")
