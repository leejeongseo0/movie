# main.py
# 어제의 박스오피스를 KOBIS API에서 가져와 보여주는 Streamlit 앱입니다.

import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# --------------------------------------------------
# 1. 페이지 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")
st.caption("영화진흥위원회 KOBIS 일일 박스오피스 기준")


# --------------------------------------------------
# 2. 한국 시간 기준으로 '어제' 계산
# --------------------------------------------------
# Streamlit Cloud 서버의 시간이 한국 시간이 아닐 수 있기 때문에
# 서버의 현재 시간을 그대로 사용하지 않고 한국 시간(KST)을 사용합니다.

KST = ZoneInfo("Asia/Seoul")

today_kst = datetime.now(KST).date()
yesterday_kst = today_kst - timedelta(days=1)

# KOBIS API가 요구하는 YYYYMMDD 형식으로 변환
target_date = yesterday_kst.strftime("%Y%m%d")

# 화면에 보여줄 날짜
display_date = yesterday_kst.strftime("%Y년 %m월 %d일")


# --------------------------------------------------
# 3. KOBIS API 주소와 인증키 가져오기
# --------------------------------------------------

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

# 인증키는 코드에 직접 적지 않고 Streamlit Secrets에서 가져옵니다.
# Streamlit Cloud의 Secrets에 다음처럼 저장해야 합니다.
#
# KOBIS_KEY = "발급받은_인증키"

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]
except Exception:
    st.error("KOBIS 인증키를 불러오지 못했습니다.")
    st.info(
        "Streamlit Cloud의 앱 설정에서 Secrets를 열고 "
        "`KOBIS_KEY`라는 이름으로 인증키를 등록했는지 확인해 주세요."
    )
    st.stop()


# --------------------------------------------------
# 4. KOBIS API 요청
# --------------------------------------------------

params = {
    "key": KOBIS_KEY,
    "targetDt": target_date
}

try:
    response = requests.get(
        API_URL,
        params=params,
        timeout=10
    )

    # HTTP 상태 코드가 200이 아니면 오류로 처리합니다.
    response.raise_for_status()

    data = response.json()

except requests.exceptions.Timeout:
    st.error("KOBIS API 요청 시간이 초과되었습니다.")
    st.info(
        "인터넷 연결 상태나 KOBIS 서버 상태를 확인한 뒤 "
        "잠시 후 다시 실행해 주세요."
    )
    st.stop()

except requests.exceptions.RequestException as e:
    st.error("KOBIS API에 요청하는 중 오류가 발생했습니다.")
    st.info(
        "KOBIS API 주소, 인터넷 연결 상태 또는 KOBIS 서버 상태를 "
        "확인해 주세요."
    )
    st.stop()

except ValueError:
    st.error("KOBIS API가 올바른 JSON 데이터를 반환하지 않았습니다.")
    st.info(
        "KOBIS API 서버의 응답 상태를 확인한 뒤 잠시 후 다시 시도해 주세요."
    )
    st.stop()


# --------------------------------------------------
# 5. KOBIS가 반환한 오류 확인
# --------------------------------------------------
# KOBIS는 인증키가 잘못된 경우에도 HTTP 상태코드가 200일 수 있습니다.
# 따라서 response.raise_for_status()만으로는 인증 오류를 잡을 수 없습니다.
#
# 정상적인 경우:
# boxOfficeResult → dailyBoxOfficeList
#
# 오류인 경우:
# faultInfo
#
# 따라서 faultInfo가 있는지 먼저 확인합니다.

if "faultInfo" in data:
    fault_info = data["faultInfo"]

    error_code = fault_info.get("errorCode", "알 수 없음")
    error_message = fault_info.get(
        "message",
        "KOBIS API에서 오류가 발생했습니다."
    )

    st.error("KOBIS API에서 오류가 반환되었습니다.")

    st.warning(
        f"오류 코드: {error_code}\n\n"
        f"오류 내용: {error_message}"
    )

    st.info(
        "다음 내용을 확인해 주세요.\n\n"
        "• Streamlit Secrets에 KOBIS_KEY가 정확히 등록되어 있는지\n"
        "• 인증키 앞뒤에 불필요한 공백이 없는지\n"
        "• KOBIS에서 발급받은 인증키가 정상적으로 사용 가능한지"
    )

    st.stop()


# --------------------------------------------------
# 6. 박스오피스 데이터 가져오기
# --------------------------------------------------

box_office_result = data.get("boxOfficeResult")

if not box_office_result:
    st.error("KOBIS 박스오피스 데이터를 찾을 수 없습니다.")
    st.info(
        "KOBIS API의 응답 구조가 정상적인지 확인하거나 "
        "잠시 후 다시 시도해 주세요."
    )
    st.stop()


movie_list = box_office_result.get("dailyBoxOfficeList", [])


# 영화 목록이 비어 있는 경우
if not movie_list:
    st.warning(
        f"{display_date}의 박스오피스 영화 목록이 없습니다."
    )

    st.info(
        "다음 내용을 확인해 주세요.\n\n"
        "• KOBIS에서 해당 날짜의 일별 박스오피스가 집계되었는지\n"
        "• 조회 날짜가 정상적으로 계산되었는지\n"
        "• KOBIS API 서버에 일시적인 문제가 없는지\n"
        "• 잠시 후 다시 실행해 보기"
    )

    st.stop()


# --------------------------------------------------
# 7. 데이터를 표로 만들기
# --------------------------------------------------

df = pd.DataFrame(movie_list)

# KOBIS에서 숫자도 문자열로 보내므로 숫자로 변환합니다.
numeric_columns = [
    "rank",
    "audiCnt",
    "audiAcc",
    "scrnCnt"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# 화면에 표시할 열만 선택
display_df = df[
    [
        "rank",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()


# 열 이름을 한국어로 변경
display_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]


# 숫자를 보기 편하게 표시
display_df["관객수"] = display_df["관객수"].map(
    lambda x: f"{int(x):,}" if pd.notna(x) else "-"
)

display_df["누적관객"] = display_df["누적관객"].map(
    lambda x: f"{int(x):,}" if pd.notna(x) else "-"
)

display_df["스크린수"] = display_df["스크린수"].map(
    lambda x: f"{int(x):,}" if pd.notna(x) else "-"
)


# --------------------------------------------------
# 8. 조회 날짜 표시
# --------------------------------------------------

st.subheader(f"📅 {display_date}")

st.caption(
    "※ 관객수는 해당 날짜의 관객수이며, 누적관객은 해당 날짜까지의 누적 관객수입니다."
)


# --------------------------------------------------
# 9. 1위 영화 정보
# --------------------------------------------------

first_movie = df.iloc[0]

first_movie_name = first_movie["movieNm"]
first_movie_audience = int(first_movie["audiCnt"])
first_movie_acc = int(first_movie["audiAcc"])
first_movie_screen = int(first_movie["scrnCnt"])


st.subheader(f"🏆 1위: {first_movie_name}")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="어제 관객수",
        value=f"{first_movie_audience:,}명"
    )

with col2:
    st.metric(
        label="누적 관객수",
        value=f"{first_movie_acc:,}명"
    )

with col3:
    st.metric(
        label="스크린수",
        value=f"{first_movie_screen:,}개"
    )


# --------------------------------------------------
# 10. 관객수 상위 5편 막대그래프
# --------------------------------------------------

st.subheader("📊 관객수 상위 5편")

top5 = df.head(5).copy()

# 그래프에서 사용할 숫자 데이터
top5["audiCnt"] = pd.to_numeric(
    top5["audiCnt"],
    errors="coerce"
)

# 영화명이 긴 경우에도 그래프에서 잘 보이도록
# 영화명과 관객수를 사용합니다.
chart_data = top5[
    ["movieNm", "audiCnt"]
].set_index("movieNm")

st.bar_chart(
    chart_data,
    x_label="영화",
    y_label="관객수"
)


# --------------------------------------------------
# 11. 전체 박스오피스 표
# --------------------------------------------------

st.subheader("🎞️ 전체 박스오피스")

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 12. 출처
# --------------------------------------------------

st.caption(
    "출처: 영화진흥위원회 영화관입장권통합전산망(KOBIS) 일일 박스오피스 Open API"
)
