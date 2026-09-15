```python
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ============================================================
# 1. 페이지 기본 설정
# ============================================================

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)


# ============================================================
# 2. 영화관 느낌의 검은색 디자인
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #080808;
        color: white;
    }

    h1, h2, h3 {
        color: white !important;
    }

    p, span, label {
        color: #d0d0d0;
    }

    [data-testid="stMetric"] {
        background-color: #151515;
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 20px;
    }

    [data-testid="stMetricLabel"] {
        color: #aaaaaa !important;
    }

    [data-testid="stMetricValue"] {
        color: white !important;
    }

    .movie-card {
        background-color: #151515;
        border: 1px solid #303030;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 20px;
        text-align: center;
    }

    .movie-title {
        color: white;
        font-size: 16px;
        font-weight: bold;
        margin-top: 8px;
        margin-bottom: 6px;
    }

    .movie-audience {
        color: #aaaaaa;
        font-size: 14px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 3. 제목
# ============================================================

st.title("🎬 어제의 박스오피스")
st.caption("영화진흥위원회 영화관입장권통합전산망(KOBIS) 기준")


# ============================================================
# 4. 한국 시간 기준으로 어제 날짜 계산
# ============================================================

# Streamlit Cloud 서버는 한국 시간이 아닐 수 있습니다.
# 따라서 반드시 한국 시간(Asia/Seoul)을 사용합니다.

KST = ZoneInfo("Asia/Seoul")

today_kst = datetime.now(KST).date()

yesterday_kst = today_kst - timedelta(days=1)

target_date = yesterday_kst.strftime("%Y%m%d")

display_date = yesterday_kst.strftime("%Y년 %m월 %d일")


# ============================================================
# 5. KOBIS API 주소
# ============================================================

DAILY_BOXOFFICE_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

MOVIE_INFO_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "movie/searchMovieInfo.json"
)


# ============================================================
# 6. Secrets에서 KOBIS 인증키 가져오기
# ============================================================

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]

except Exception:
    st.error("KOBIS 인증키를 찾을 수 없습니다.")

    st.info(
        "Streamlit Cloud의 Settings → Secrets에서 "
        "KOBIS_KEY를 등록했는지 확인해 주세요."
    )

    st.stop()


# ============================================================
# 7. 어제의 박스오피스 API 요청
# ============================================================

params = {
    "key": KOBIS_KEY,
    "targetDt": target_date
}

try:

    response = requests.get(
        DAILY_BOXOFFICE_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

except requests.exceptions.Timeout:

    st.error("KOBIS API 요청 시간이 초과되었습니다.")

    st.info(
        "인터넷 연결 상태 또는 KOBIS 서버 상태를 확인한 후 "
        "잠시 뒤 다시 실행해 주세요."
    )

    st.stop()

except requests.exceptions.RequestException:

    st.error("KOBIS API 요청에 실패했습니다.")

    st.info(
        "KOBIS API 주소, 인터넷 연결 상태 또는 "
        "KOBIS 서버 상태를 확인해 주세요."
    )

    st.stop()

except ValueError:

    st.error("KOBIS API가 올바른 데이터를 반환하지 않았습니다.")

    st.info(
        "KOBIS 서버의 응답 상태를 확인한 후 "
        "잠시 뒤 다시 실행해 주세요."
    )

    st.stop()


# ============================================================
# 8. KOBIS faultInfo 확인
# ============================================================

# KOBIS는 인증키가 틀려도 HTTP 상태코드가 200일 수 있습니다.
# 따라서 faultInfo가 있는지 반드시 확인합니다.

if "faultInfo" in data:

    fault_info = data["faultInfo"]

    error_code = fault_info.get(
        "errorCode",
        "알 수 없음"
    )

    error_message = fault_info.get(
        "message",
        "KOBIS API 오류"
    )

    st.error("KOBIS API에서 오류를 반환했습니다.")

    st.warning(
        f"오류 코드: {error_code}\n\n"
        f"오류 내용: {error_message}"
    )

    st.info(
        "다음 내용을 확인해 주세요.\n\n"
        "1. Streamlit Secrets에 KOBIS_KEY가 정확히 등록되어 있는지\n"
        "2. 인증키 앞뒤에 공백이 없는지\n"
        "3. KOBIS에서 발급받은 인증키가 정상적으로 작동하는지"
    )

    st.stop()


# ============================================================
# 9. 박스오피스 결과 확인
# ============================================================

box_office_result = data.get("boxOfficeResult")

if not box_office_result:

    st.error("박스오피스 결과를 찾을 수 없습니다.")

    st.info(
        "KOBIS API 응답을 확인하거나 잠시 후 다시 실행해 주세요."
    )

    st.stop()


movie_list = box_office_result.get(
    "dailyBoxOfficeList",
    []
)


if not movie_list:

    st.warning(
        f"{display_date}의 영화 목록이 없습니다."
    )

    st.info(
        "다음 내용을 확인해 주세요.\n\n"
        "1. KOBIS에서 해당 날짜의 박스오피스가 집계되었는지\n"
        "2. KOBIS API 서버에 문제가 없는지\n"
        "3. 잠시 후 다시 실행해 보기"
    )

    st.stop()


# ============================================================
# 10. 박스오피스 DataFrame 만들기
# ============================================================

df = pd.DataFrame(movie_list)


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


# ============================================================
# 11. 어제의 박스오피스 날짜
# ============================================================

st.subheader(f"📅 {display_date}")

st.caption(
    "관객수는 해당 날짜의 관객수이며, "
    "누적관객은 해당 날짜까지의 누적 관객수입니다."
)


# ============================================================
# 12. 1위 영화
# ============================================================

first_movie = df.iloc[0]

first_movie_name = first_movie["movieNm"]

first_movie_audience = int(
    first_movie["audiCnt"]
)

first_movie_acc = int(
    first_movie["audiAcc"]
)

first_movie_screen = int(
    first_movie["scrnCnt"]
)


st.subheader(f"🏆 1위: {first_movie_name}")


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "어제 관객수",
        f"{first_movie_audience:,}명"
    )


with col2:

    st.metric(
        "누적 관객수",
        f"{first_movie_acc:,}명"
    )


with col3:

    st.metric(
        "스크린수",
        f"{first_movie_screen:,}개"
    )


# ============================================================
# 13. 관객수 상위 5편 그래프
# ============================================================

st.subheader("📊 관객수 상위 5편")


top5 = df.head(5).copy()


top5["audiCnt"] = pd.to_numeric(
    top5["audiCnt"],
    errors="coerce"
)


chart_data = top5[
    ["movieNm", "audiCnt"]
].set_index("movieNm")


st.bar_chart(
    chart_data,
    x_label="영화",
    y_label="관객수"
)


# ============================================================
# 14. 전체 박스오피스 표
# ============================================================

st.subheader("🎞️ 전체 박스오피스")


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


display_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]


display_df["관객수"] = display_df["관객수"].map(
    lambda x: f"{int(x):,}" if pd.notna(x) else "-"
)


display_df["누적관객"] = display_df["누적관객"].map(
    lambda x: f"{int(x):,}" if pd.notna(x) else "-"
)


display_df["스크린수"] = display_df["스크린수"].map(
    lambda x: f"{int(x):,}" if pd.notna(x) else "-"
)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 15. 역대 1000만 관객 영화
# ============================================================

st.divider()

st.header("🏆 역대 1000만 관객 영화")

st.caption(
    "누적 관객수 1,000만 명 이상을 기록한 영화"
)


# ============================================================
# 16. 역대 1000만 영화 목록
# ============================================================
#
# KOBIS 영화코드와 영화명을 이용합니다.
# 누적관객수는 KOBIS 자료를 기준으로 정리한 값입니다.
#
# 새로운 1000만 영화가 추가되면 이 목록에 추가할 수 있습니다.
# ============================================================

TEN_MILLION_MOVIES = [

    ("명량", "20146141", 17613682),

    ("극한직업", "20182530", 16264944),

    ("신과함께-죄와 벌", "20150976", 14414658),

    ("국제시장", "20124079", 14257115),

    ("베테랑", "20142408", 13414358),

    ("서울의 봄", "20212866", 13128537),

    ("아바타", "20096262", 13333000),

    ("도둑들", "20112871", 12983744),

    ("7번방의 선물", "20127592", 12811206),

    ("알라딘", "20183867", 12797715),

    ("암살", "20148851", 12705700),

    ("범죄도시2", "20210028", 12693201),

    ("광해, 왕이 된 남자", "20124021", 12319542),

    ("신과함께-인과 연", "20180613", 12274906),

    ("택시운전사", "20162545", 12189609),

    ("파묘", "20233033", 11912444),

    ("태극기 휘날리며", "20040012", 11746135),

    ("부산행", "20156564", 11565479),

    ("변호인", "20124050", 11374879),

    ("해운대", "20090046", 11453134),

    ("어벤져스: 인피니티 워", "20177478", 11212710),

    ("실미도", "20030046", 11081000),

    ("괴물", "20060135", 10917458),

    ("아바타: 물의 길", "20223279", 10805065),

    ("왕의 남자", "20051236", 10514100),

    ("기생충", "20183782", 10312865),

    ("인터스텔라", "20128479", 10342523),

    ("겨울왕국", "20139220", 10296101),
]


# ============================================================
# 17. DataFrame으로 변환
# ============================================================

million_df = pd.DataFrame(
    TEN_MILLION_MOVIES,
    columns=[
        "영화명",
        "movieCd",
        "누적관객"
    ]
)


# 누적관객수가 많은 순서로 정렬

million_df = million_df.sort_values(
    "누적관객",
    ascending=False
).reset_index(drop=True)


# ============================================================
# 18. 포스터 가져오기
# ============================================================

@st.cache_data(ttl=86400)
def get_movie_info(movie_code):

    params = {
        "key": KOBIS_KEY,
        "movieCd": movie_code
    }

    try:

        response = requests.get(
            MOVIE_INFO_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        result = response.json()

        movie_info_result = result.get(
            "movieInfoResult",
            {}
        )

        movie_info = movie_info_result.get(
            "movieInfo",
            {}
        )

        return movie_info

    except Exception:

        return {}


# ============================================================
# 19. 영화 포스터 표시
# ============================================================
#
# KOBIS 영화정보 API의 영화 정보에서
# posterUrl이 제공되는 경우 사용합니다.
#
# 포스터 주소가 없는 영화는
# 영화 아이콘으로 대신 표시합니다.
# ============================================================

for start in range(
    0,
    len(million_df),
    5
):

    row = million_df.iloc[
        start:start + 5
    ]

    columns = st.columns(5)


    for column, (index, movie) in zip(
        columns,
        row.iterrows()
    ):

        with column:

            movie_name = movie["영화명"]

            movie_code = movie["movieCd"]

            audience = int(
                movie["누적관객"]
            )


            # KOBIS에서 영화 정보 가져오기

            movie_info = get_movie_info(
                movie_code
            )


            # 포스터 주소 확인

            poster_url = movie_info.get(
                "posterUrl",
                ""
            )


            # 포스터가 있으면 표시

            if poster_url:

                st.image(
                    poster_url,
                    use_container_width=True
                )

            else:

                st.markdown(
                    """
                    <div style="
                        height: 300px;
                        background-color: #222222;
                        border-radius: 10px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 55px;
                    ">
                    🎬
                    </div>
                    """,
                    unsafe_allow_html=True
                )


            # 영화 이름과 관객수

            st.markdown(
                f"""
                <div class="movie-card">

                    <div class="movie-title">
                        {movie_name}
                    </div>

                    <div class="movie-audience">
                        누적 {audience:,}명
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# 20. 출처
# ============================================================

st.caption(
    "출처: 영화진흥위원회 영화관입장권통합전산망(KOBIS)"
)
```
