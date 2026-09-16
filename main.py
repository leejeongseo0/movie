import datetime
from zoneinfo import ZoneInfo
import requests
import pandas as pd
import streamlit as st

# 1. 페이지 제목 및 레이아웃 설정 (영화관 테마 아이콘 설정)
st.set_page_config(
    page_title="일일 박스오피스 극장",
    page_icon="🍿",
    layout="wide"
)

# 2. 커스텀 CSS - 팝콘과 4D 안경 모티프 및 영화관 느낌의 다크 스타일 연출
st.markdown("""
<style>
    /* 배경 및 분위기 연출 */
    .stApp {
        background-color: #0e0e12;
        color: #f1f1f1;
    }
    
    /* 팝콘, 4D 안경 메인 헤더 배너 */
    .cinema-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #1f1c2c 0%, #928DAB 100%);
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2);
    }
    
    /* 영화 카드 스타일링 */
    .movie-card {
        background-color: #1a1a24;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# 팝콘 & 4D 안경 헤더 장식 출력
st.markdown("""
<div class="cinema-header">
    <h1>🍿 🕶️ 영화관 일일 박스오피스 🕶️ 🍿</h1>
    <p>4D 안경을 쓰고 팝콘을 먹으며 확인하는 최신 박스오피스 순위!</p>
</div>
""", unsafe_allow_html=True)

# 3. 인증키 가져오기 (Secrets 가상 금고에서 가져옴)
try:
    API_KEY = st.secrets["KOBIS_KEY"]
except Exception:
    API_KEY = None

# 4. 날짜 계산 (파이썬 기본 내장 ZoneInfo 모듈 사용으로 한국 시간 기준 '어제' 추출)
now_korea = datetime.datetime.now(ZoneInfo('Asia/Seoul'))
yesterday_korea = now_korea - datetime.timedelta(days=1)
target_dt = yesterday_korea.strftime('%Y%m%d')
formatted_date = yesterday_korea.strftime('%Y년 %m월 %d일')

st.write(f"📅 **조회 기준일자 (한국 시간):** {formatted_date}")

# 5. API 인증키 검증 및 데이터 요청 처리
if not API_KEY:
    st.error("🔑 **API 키가 설정되지 않았습니다!**")
    st.info("""
    **확인 방법:**
    1. Streamlit Cloud의 **App settings -> Secrets** 메뉴로 이동하세요.
    2. 아래 형식으로 KOBIS 인증키를 추가해 주세요:
       ```toml
       KOBIS_KEY = "발급받은_인증키_입력"
       ```
    """)
else:
    # API 요청 URL 및 파라미터 준비
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": API_KEY,
        "targetDt": target_dt
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # 에러 응답(faultInfo) 확인 및 리스트 존재 여부 체크
        if "faultInfo" in data:
            st.error("⚠️ **영화진흥위원회 API 응답 오류가 발생했습니다.**")
            st.warning(f"오류 메시지: {data['faultInfo'].get('message', '알 수 없는 오류')}")
            st.info("💡 **확인 사항:** 입력하신 `KOBIS_KEY` 인증키가 올바른지 확인해 주세요.")
        elif "boxOfficeResult" in data and "dailyBoxOfficeList" in data["boxOfficeResult"]:
            box_office_list = data["boxOfficeResult"]["dailyBoxOfficeList"]
            
            if not box_office_list:
                st.warning("🎬 **선택한 날짜의 박스오피스 데이터가 비어 있습니다.**")
                st.info("💡 집계 작업 중이거나 해당 날짜의 데이터가 아직 업데이트되지 않았을 수 있습니다.")
            else:
                # 판다스 데이터프레임 변환
                df = pd.DataFrame(box_office_list)
                
                # 수치 데이터 형변환 (문자열 -> 숫자)
                df['rank'] = df['rank'].astype(int)
                df['audiCnt'] = df['audiCnt'].astype(int)
                df['audiAcc'] = df['audiAcc'].astype(int)
                df['scrnCnt'] = df['scrnCnt'].astype(int)
                
                # -------------------------------------------------------------
                # 🏆 1위 영화 지표 카드 (Metric 3장)
                # -------------------------------------------------------------
                top_movie = df.iloc[0]
                st.subheader(f"🥇 어제의 1위 영화: {top_movie['movieNm']}")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("🎬 일일 관객수", f"{top_movie['audiCnt']:,} 명")
                col2.metric("🍿 누적 관객수", f"{top_movie['audiAcc']:,} 명")
                col3.metric("🖥️ 스크린수", f"{top_movie['scrnCnt']:,} 개")
                
                st.divider()
                
                # -------------------------------------------------------------
                # 📊 관객수 상위 5편 막대그래프
                # -------------------------------------------------------------
                st.subheader("📊 관객수 상위 5개 영화")
                top5_df = df.head(5)[['movieNm', 'audiCnt']].set_index('movieNm')
                st.bar_chart(top5_df)
                
                st.divider()
                
                # -------------------------------------------------------------
                # 📋 전체 순위표 (테이블)
                # -------------------------------------------------------------
                st.subheader("📋 전체 박스오피스 순위")
                
                # 컬럼명 한국어 변경 및 필요한 열만 선별
                display_df = df[['rank', 'movieNm', 'openDt', 'audiCnt', 'audiAcc', 'scrnCnt']].copy()
                display_df.columns = ['순위', '영화명', '개봉일', '관객수', '누적관객수', '스크린수']
                
                # 숫자 포맷 변경하여 표시
                st.dataframe(
                    display_df,
                    column_config={
                        "관객수": st.column_config.NumberColumn(format="%d 명"),
                        "누적관객수": st.column_config.NumberColumn(format="%d 명"),
                        "스크린수": st.column_config.NumberColumn(format="%d 개")
                    },
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.error("⚠️ **예상치 못한 응답 구조입니다.**")
            st.info("KOBIS API 서버 상태를 확인해 주세요.")
            
    except requests.exceptions.RequestException:
        st.error("🌐 **네트워크 통신 오류가 발생했습니다.**")
        st.info("인터넷 연결 상태나 KOBIS API 서버 응답 유무를 확인해 주세요.")

# -------------------------------------------------------------
# 🍿 역대 1,000만 관객 돌파 대표 영화 명예의 전당
# -------------------------------------------------------------
st.divider()
st.subheader("🕶️ 역대 1,000만 명작 명예의 전당 🍿")
st.write("한국 극장가를 뜨겁게 달궜던 대표 천만 영화들입니다!")

hall_of_fame = [
    {"title": "명량 (2014)", "views": "1,761만 명", "img": "https://encrypted-tbn1.gstatic.com/licensed-image?q=tbn:ANd9GcScDrj-0T082a0ilx7WWN27rY4f--OUO8C_AgXisyCT9afv7z836tb0NHM6dCgZzEWe8btFQGMWWMweL1A"},
    {"title": "극한직업 (2019)", "views": "1,626만 명", "img": "https://dimg.donga.com/wps/SPORTS/IMAGE/2019/02/06/93399794.11.jpg"},
    {"title": "신과함께-죄와 벌 (2017)", "views": "1,441만 명", "img": "https://encrypted-tbn0.gstatic.com/licensed-image?q=tbn:ANd9GcSfKC4nZE8sxg7P6dDQJhqgs5MCwgtDoBN_kx6tXRlbuqDnGdkKj4isJ45KpfXfn6mbgM195q5NHuSFDak"},
    {"title": "태극기 휘날리며 (2004)", "views": "1,174만 명", "img": "https://encrypted-tbn0.gstatic.com/licensed-image?q=tbn:ANd9GcQX4wr7nN8vctb3XBWcQAuq3xke22pXM0MYaYthKXUU75bSDXAfBSy6n7drPpjBH9CHb-psdt1hLevxOwU"}
]

fame_cols = st.columns(len(hall_of_fame))

for idx, movie in enumerate(hall_of_fame):
    with fame_cols[idx]:
        st.image(movie["img"], use_container_width=True)
        st.caption(f"**{movie['title']}**\n\n🎉 {movie['views']}")
