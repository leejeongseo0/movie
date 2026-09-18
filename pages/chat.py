import streamlit as st
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(page_title="밤하늘의 선율 - 감성 음악 AI", page_icon="🌙", layout="centered")

# Custom CSS: 낭만적인 밤하늘 분위기의 배경 및 디자인 설정
st.markdown("""
    <style>
    /* 전체 배경을 어두운 밤하늘 그라데이션으로 설정 */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%);
        color: #e2e8f0;
    }
    
    /* 채팅 메시지 박스 스타일링 */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
        backdrop-filter: blur(5px);
    }
    
    /* 입력창 스타일링 */
    .stChatInputContainer {
        border-radius: 20px;
    }
    
    /* 제목 텍스트 스타일 */
    h1 {
        color: #f472b6 !important;
        font-weight: 300 !important;
        text-shadow: 0 0 10px rgba(244, 114, 182, 0.5);
    }
    </style>
""", unsafe_allow_html=True)  # <-- 오타 수정 부분 (unsafe_allow_keywords -> unsafe_allow_html)

st.title("🌙 밤하늘의 선율")
st.caption("당신의 마음과 계절, 순간의 감정에 어울리는 음악을 띄워드립니다.")

# 비밀 금고(secrets) 점검 및 API 키 접속
if "GEMINI_API_KEY" not in st.secrets:
    st.error("secrets.toml 파일 또는 Streamlit Secrets에 GEMINI_API_KEY가 설정되지 않았습니다.")
    st.stop()

client = OpenAI(
    api_key=st.secrets["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# AI의 성격: 감성적이고 낭만적인 음악 추천가
SYSTEM_PROMPT = (
    "너는 깊은 밤 마음을 다독여주는 낭만적이고 감성적인 음악 추천가야. "
    "상대방의 기분, 분위기, 상황을 들으면 마음을 울리는 좋은 노래를 시적이고 따뜻한 말투로 추천해줘. "
    "노래의 가사 일부나 곡에 담긴 분위기를 아름다운 문장으로 풀어 설명해줘."
)

# 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# 이전 대화 출력
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 사용자 입력
user_input = st.chat_input("지금 어떤 마음이신가요? 기분이나 분위기를 편하게 들려주세요...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model="gemini-1.5-flash",
                messages=st.session_state.messages,
                stream=True,
            )
            answer = st.write_stream(
                chunk.choices[0].delta.content or ""
                for chunk in stream if chunk.choices
            )
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"선율을 불러오는 중에 문제가 발생했습니다: {e}")
