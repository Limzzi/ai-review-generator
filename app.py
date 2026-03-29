import json
import streamlit as st
from review_generator import generate_review

st.set_page_config(
    page_title="AI 제품 리뷰 생성기",
    page_icon="📝",
    layout="centered"
)

if "example_index" not in st.session_state:
    st.session_state.example_index = 0

examples = {
    {"product_name": "아이폰 15", "target_audience": "20대", "review_tone": "솔직한 후기"},
    {"product_name": "닌텐도 스위치 OLED", "target_audience": "10대", "review_tone": "신나는 후기"},
    {"product_name": "기계식 키보드", "target_audience": "개발자", "review_tone": "담백한 후기"}
}

def load_example(index: int):
    example = examples[index]
    st.session_state.product_name = example["product_name"]
    st.session_state.target_audience = example["target_audience"]
    st.session_state.review_tone = example["review_tone"]
    st.session_state.desired_rating = 4

st.title("📝 AI 제품 리뷰 생성기")
st.write("상품명, 타겟, 톤을 입력하면 AI가 구조화된 리뷰를 생성합니다.")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("예시 입력1"):
        load_example(0)
with col2:
    if st.button("예시 입력2"):
        load_example(1)

if st.button("예시 입력 3"):
    load_example(2)

with st.form("review_form"):
    product_name = st.text_input(
        "상품명",
        placeholder="예: 아이폰 15",
        key="product_name"
    )
    target_audience = st.text_input(
        "타겟",
        placeholder="예: 20대",
        key="target_audience"
    )
    review_tone = st.text_input(
        "톤",
        placeholder="예: 솔직한 후기",
        key="review_tone"
    )
    desired_rating = st.slider(
        "희망 평점",
        min_value=1,
        max_value=5,
        value=4,
        help="AI가 이 평점에 가깝게 리뷰를 작성하도록 유도합니다.",
        key="desired_rating"
    )

    submitted = st.form_submit_button("리뷰 생성")

if submitted:
    if not product_name or not target_audience or not review_tone:
        st.error("모든 입력값을 채워주세요.")
    else:
        with st.spinner("AI가 리뷰를 생성하는 중입니다..."):
            result = generate_review(
                product_name=product_name,
                target_audience=target_audience,
                review_tone=review_tone,
                desired_rating=desired_rating,
                max_retry_count=3
            )

        st.subheader("생성 결과")

        if result["success"]:
            review_data = result["review_data"]

            st.success(f"검증 통과! (시도 횟수: {result['attempt']})")

            with st.container(border=True):
                st.markdown(f"## {review_data['title']}")
                st.metric("평점", f"{review_data['rating']} / 5")

                pros_col, cons_col = st.columns(2)

                with pros_col:
                    st.markdown("### 👍 장점")
                    for item in review_data["pros"]:
                        st.write(f"- {item}")

                with cons_col:
                    st.markdown("### 👎 단점")
                    for item in review_data["cons"]:
                        st.write(f"- {item}")

                st.markdown("### 📌 요약")
                st.write(review_data["summary"])

            with st.expander("JSON 데이터 보기"):
                st.code(
                    json.dumps(review_data, ensure_ascii=False, indent=4),
                    language="json"
                )

            with st.expander("생성 프롬프트 보기"):
                st.text(result["prompt"])

            with st.expander("원본 응답 보기"):
                st.text(result["raw_response"])

            with st.expander("정제된 응답 보기"):
                st.text(result["sanitized_response"])

        else:
            st.error("리뷰 생성에 실패했습니다.")
            st.write("**오류 목록**")
            for error in result["errors"]:
                st.write(f"- {error}")

            if result["raw_response"]:
                with st.expander("원본 응답 보기"):
                    st.text(result["raw_response"])

            if result["sanitized_response"]:
                with st.expander("정제된 응답 보기"):
                    st.text(result["sanitized_response"])

st.divider()
st.caption("Prompt Engineering Practice Project")