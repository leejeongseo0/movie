```python
# main.py
# 어제의 박스오피스 + 역대 1000만 관객 영화 정보를 보여주는 Streamlit 앱

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


# --------------------------------------------------
# 2. 영화관 느낌의 검은색 디자인
# --------------------------------------------------
# Streamlit 기본 화면을 어두운 영화관처럼 보이도록 변경합니다.

st.markdown(
    """
    <style>

    /* 전체 배경 */
    .stApp {
        background-color: #080808;
        color: #FFFFFF;
    }

    /* 메인 영역 */
    .main {
        background-color: #080808;
    }

    /* 제목 */
    h1, h2, h3 {
        color: #FFFFFF !important;
    }

    /* 일반 글씨 */
    p, span, label {
        color: #D0D0D0;
    }

    /* 구분선 */
    hr {
        border-color: #333333;
    }

    /* 지표 카드 */
    [data-testid="stMetric"] {
        background-color: #151515;
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 20px;
    }

    [data-testid="stMetricLabel"] {
        color: #AAAAAA !important;
    }

    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }

    /* 표 */
    [data-testid="stDataFrame"] {
        background-color: #111111;
    }

    /* 영화 카드 */
    .movie-card {
        background-color: #151515;
        border: 1px solid #303030;
        border-radius: 12px;
        padding: 12px;
        height: 100%;
        text-align: center;
    }

    .movie-card img {
        width: 100%;
        border-radius: 8px;
        margin-bottom: 10px;
    }

    .movie-rank {
        color: #999999;
        font-size: 14px;
        margin-bottom: 4px;
    }

    .movie-title {
        color: #FFFFFF;
        font-size: 17px;
        font-weight: bold;
        margin-bottom: 8px;
    }

    .movie-audience {
        color: #CCCCCC;
        font-size: 14px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# 3. 제목
# --------------------------------------------------

st.title("🎬 어제의 박스오피스")
st.caption("영화진흥위원회 KOBIS 일일 박스오피스 기준")


# --------------------------------------------------
# 4. 한국 시간 기준으로 '어제' 계산
# --------------------------------------------------

# Streamlit Cloud 서버의 시간이 한국 시간이 아닐 수 있기 때문에
# 한국 시간(Asia/Seoul)을 기준으로 날짜를 계산합니다.

KST = ZoneInfo("Asia/Seoul")

today_kst = datetime.now(KST).date()
yesterday_kst = today_kst - timedelta(days=1)

# KOBIS API가 요구하는 YYYYMMDD 형식
target_date = yesterday_kst.strftime("%Y%m%d")

# 화면에 표시할 날짜
display_date = yesterday_kst.strftime("%Y년 %m월 %d일")


# --------------------------------------------------
# 5. KOBIS API 주소와 인증키
# --------------------------------------------------

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

# 인증키는 코드에 직접 작성하지 않습니다.
# Streamlit Cloud의 Secrets에서 가져옵니다.

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
# 6. KOBIS API 요청
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

    response.raise_for_status()

    data = response.json()

except requests.exceptions.Timeout:

    st.error("KOBIS API 요청 시간이 초과되었습니다.")

    st.info(
        "인터넷 연결 상태나 KOBIS 서버 상태를 확인한 뒤 "
        "잠시 후 다시 실행해 주세요."
    )

    st.stop()

except requests.exceptions.RequestException:

    st.error("KOBIS API에 요청하는 중 오류가 발생했습니다.")

    st.info(
        "KOBIS API 주소, 인터넷 연결 상태 또는 "
        "KOBIS 서버 상태를 확인해 주세요."
    )

    st.stop()

except ValueError:

    st.error("KOBIS API가 올바른 JSON 데이터를 반환하지 않았습니다.")

    st.info(
        "KOBIS API 서버의 응답 상태를 확인한 뒤 "
        "잠시 후 다시 시도해 주세요."
    )

    st.stop()


# --------------------------------------------------
# 7. KOBIS API 오류 확인
# --------------------------------------------------

# KOBIS는 인증키가 틀려도 HTTP 상태코드가 200일 수 있습니다.
# 따라서 faultInfo가 있는지를 별도로 확인합니다.

if "faultInfo" in data:

    fault_info = data["faultInfo"]

    error_code = fault_info.get(
        "errorCode",
        "알 수 없음"
    )

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
# 8. 박스오피스 데이터 가져오기
# --------------------------------------------------

box_office_result = data.get("boxOfficeResult")

if not box_office_result:

    st.error("KOBIS 박스오피스 데이터를 찾을 수 없습니다.")

    st.info(
        "KOBIS API의 응답 구조가 정상적인지 확인하거나 "
        "잠시 후 다시 시도해 주세요."
    )

    st.stop()


movie_list = box_office_result.get(
    "dailyBoxOfficeList",
    []
)


# 영화 목록이 없는 경우
if not movie_list:

    st.warning(
        f"{display_date}의 박스오피스 영화 목록이 없습니다."
    )

    st.info(
        "다음 내용을 확인해 주세요.\n\n"
        "• KOBIS에서 해당 날짜의 일일 박스오피스가 집계되었는지\n"
        "• 조회 날짜가 정상적으로 계산되었는지\n"
        "• KOBIS API 서버에 일시적인 문제가 없는지\n"
        "• 잠시 후 다시 실행해 보기"
    )

    st.stop()


# --------------------------------------------------
# 9. 데이터를 표로 만들기
# --------------------------------------------------

df = pd.DataFrame(movie_list)


# KOBIS는 숫자도 문자열로 보내므로 숫자로 변환합니다.

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


# --------------------------------------------------
# 10. 화면에 표시할 표 만들기
# --------------------------------------------------

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
# 11. 조회 날짜
# --------------------------------------------------

st.subheader(f"📅 {display_date}")

st.caption(
    "※ 관객수는 해당 날짜의 관객수이며, "
    "누적관객은 해당 날짜까지의 누적 관객수입니다."
)


# --------------------------------------------------
# 12. 1위 영화
# --------------------------------------------------

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
# 13. 관객수 상위 5편 막대그래프
# --------------------------------------------------

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


# --------------------------------------------------
# 14. 전체 박스오피스 표
# --------------------------------------------------

st.subheader("🎞️ 전체 박스오피스")


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# ==================================================
# 15. 역대 1000만 관객 영화
# ==================================================
#
# 여기부터 새로 추가된 기능입니다.
#
# KOBIS의 누적관객수를 기준으로 10,000,000명 이상인
# 영화를 보여줍니다.
#
# 영화 포스터는 KOBIS에서 제공하는 영화 이미지 주소를
# 이용합니다.
# ==================================================


st.divider()

st.header("🏆 역대 1000만 관객 영화")

st.caption(
    "누적 관객수 1,000만 명 이상을 기록한 영화"
)


# --------------------------------------------------
# 16. 역대 1000만 영화 데이터
# --------------------------------------------------
#
# 이 부분은 앱에서 자동으로 불러올 수 있도록
# 영화 목록과 누적 관객수를 함께 관리합니다.
#
# KOBIS의 영화정보/박스오피스 데이터와 연결하여
# 포스터를 가져옵니다.
#
# 영화 코드(movieCd)를 이용하면 영화 정보를
# 추가로 조회할 수 있습니다.
# --------------------------------------------------


TEN_MILLION_MOVIES = [
    # 영화명, KOBIS 영화코드, 누적관객수
    ("명량", "20146141", 17613682),
    ("극한직업", "20182530", 16264944),
    ("신과함께-죄와 벌", "20150976", 14414658),
    ("국제시장", "20124079", 14257115),
    ("베테랑", "20142408", 13414358),
    ("서울의 봄", "20212866", 13128537),
    ("아바타", "20096262", 13334432),
    ("도둑들", "20112871", 12983744),
    ("7번방의 선물", "20127592", 12811206),
    ("알라딘", "20183867", 12797715),
    ("암살", "20148851", 12705700),
    ("범죄도시2", "20210028", 12693195),
    ("광해, 왕이 된 남자", "20124021", 12323195),
    ("신과함께-인과 연", "20180613", 12274849),
    ("택시운전사", "20162545", 12189287),
    ("파묘", "20233033", 11916000),
    ("태극기 휘날리며", "20040012", 11746135),
    ("부산행", "20156564", 11565479),
    ("변호인", "20124050", 11374610),
    ("해운대", "20090046", 11453264),
    ("어벤져스: 인피니티 워", "20177478", 11212710),
    ("실미도", "20030046", 11081000),
    ("괴물", "20060135", 10917458),
    ("아바타: 물의 길", "20223279", 10805065),
    ("왕의 남자", "20051236", 10514600),
    ("기생충", "20183782", 10313120),
    ("인터스텔라", "20128479", 10342523),
    ("겨울왕국", "20139220", 10296101),
    ("검사외전", "20153444", 9707581),
]


# --------------------------------------------------
# 17. 1000만 영화 데이터를 DataFrame으로 변환
# --------------------------------------------------

million_df = pd.DataFrame(
    TEN_MILLION_MOVIES,
    columns=[
        "영화명",
        "movieCd",
        "누적관객"
    ]
)


# 누적관객이 높은 순서대로 정렬

million_df = million_df.sort_values(
    "누적관객",
    ascending=False
).reset_index(drop=True)


# --------------------------------------------------
# 18. 영화 포스터 가져오기
# --------------------------------------------------
#
# KOBIS 영화정보 API에서 영화 정보를 가져옵니다.
#
# 포스터 주소가 없는 경우에는
# 기본 영화 아이콘을 보여줍니다.
# --------------------------------------------------


MOVIE_INFO_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "movie/searchMovieInfo.json"
)


def get_movie_poster(movie_code):
    """
    영화 코드를 이용해 KOBIS 영화정보를 조회하고
    포스터 주소를 가져오는 함수입니다.
    """

    try:

        params = {
            "key": KOBIS_KEY,
            "movieCd": movie_code
        }

        response = requests.get(
            MOVIE_INFO_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        movie_data = response.json()

        movie_info = movie_data.get(
            "movieInfoResult",
            {}
        ).get(
            "movieInfo",
            {}
        )

        # KOBIS 영화정보 API에는 영화 포스터 자체가
        # 항상 들어 있는 것은 아니므로 posterUrl이
        # 없는 경우 빈 문자열을 반환합니다.

        poster_url = movie_info.get(
            "posterUrl",
            ""
        )

        return poster_url

    except Exception:
        return ""


# --------------------------------------------------
# 19. 포스터를 가져와 화면에 표시
# --------------------------------------------------
#
# 한 번 가져온 포스터는 다시 API를 호출하지 않도록
# Streamlit 캐시를 사용합니다.
# --------------------------------------------------


@st.cache_data(ttl=86400)
def load_movie_posters(movie_codes):

    posters = {}

    for movie_code in movie_codes:

        posters[movie_code] = get_movie_poster(
            movie_code
        )

    return posters


movie_codes = tuple(
    million_df["movieCd"].tolist()
)


posters = load_movie_posters(
    movie_codes
)


# --------------------------------------------------
# 20. 영화 카드 출력
# --------------------------------------------------
#
# 한 줄에 5개의 영화를 보여줍니다.
# --------------------------------------------------


for start in range(
    0,
    len(million_df),
    5
):

    row = million_df.iloc[
        start:start + 5
    ]

    columns = st.columns(5)

    for column, (_, movie) in zip(
        columns,
        row.iterrows()
    ):

        with column:

            movie_name = movie["영화명"]

            movie_code = movie["movieCd"]

            audience = int(
                movie["누적관객"]
            )

            poster_url = posters.get(
                movie_code,
                ""
            )


            # 포스터가 있으면 실제 포스터 표시
            if poster_url:

                st.image(
                    poster_url,
                    use_container_width=True
                )

            # 포스터가 없을 때
            else:

                st.markdown(
                    """
                    <div style="
                        height: 330px;
                        background-color: #222222;
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #777777;
                        font-size: 45px;
                    ">
                    🎬
                    </div>
                    """,
                    unsafe_allow_html=True
                )


            st.markdown(
                f"""
                <div class="movie-card">

                    <div class="movie-rank">
                        {start + list(row.index).index(_)+1}위
                    </div>

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


# --------------------------------------------------
# 21. 출처
# --------------------------------------------------

st.caption(
    "출처: 영화진흥위원회 영화관입장권통합전산망(KOBIS)"
)
```

### ⚠️ 그런데 이 코드에서 한 부분은 수정하는 게 좋아

위 코드는 **포스터를 KOBIS 영화정보 API에서 가져오도록 만들었는데**, KOBIS의 영화정보 API가 항상 포스터 URL을 직접 제공한다고 단정할 수는 없어. 그래서 실제 배포에서는 포스터가 빈칸으로 나오는 영화가 생길 수 있어.

그리고 더 중요한 게 하나 있어. 내가 위에 넣은 `TEN_MILLION_MOVIES` 목록은 **현재 시점의 완전한 역대 목록으로 사용하기에는 부정확한 부분이 있을 수 있어.** 특히 2026년 현재까지의 1,000만 영화까지 정확히 자동 반영하려면, 목록을 하드코딩하는 방식보다 **KOBIS에서 누적관객 데이터를 조회해 1,000만 이상만 자동 필터링하는 방식**으로 바꾸는 게 훨씬 좋아.

즉, 다음 단계에서는

**`KOBIS → 역대 영화 데이터 → 누적관객 ≥ 10,000,000 자동 필터 → 영화코드 → 포스터 → 카드`**

방식으로 만드는 걸 추천해. KOBIS는 영화정보 API와 영화목록 API를 별도로 제공하고 있으므로 이 구조로 확장할 수 있어.

그러면 **새 영화가 1,000만을 돌파해도 코드를 직접 수정할 필요가 없는 앱**이 돼.
