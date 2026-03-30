import json
import os

# .env 파일에서 환경변수 불러오기
from dotenv import load_dotenv

# OpenAI API 사용
from openai import OpenAI

# .env 파일 로드 (API KEY 불러오기)
load_dotenv()

# 환경 변수에서 API 키 가져오기
api_key = os.getenv("OPENAI_API_KEY")

# API 키가 없으면 에러 발생 (보안 + 안정성)
if not api_key:
    raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

# OpenAI 클라이언트 생성
client = OpenAI(api_key=api_key)


# ---------------------------------------------------
# 1. 프롬프트 생성 함수
# ---------------------------------------------------
def build_review_prompt(
    product_name: str,
    target_audience: str,
    review_tone: str,
    desired_rating: int
) -> str:
    """
    AI에게 보낼 프롬프트를 생성하는 함수

    역할:
    - 사용자 입력을 기반으로
    - JSON 형식 리뷰 생성 요청
    """

    return f"""
너는 전문적인 제품 리뷰어다.

목표:
주어진 상품에 대해 구조화된 리뷰를 작성하라.

조건:
- product: {product_name}
- target: {target_audience}
- tone: {review_tone}
- desired_rating: {desired_rating}
- rating은 desired_rating에 가깝게 작성

출력 규칙:
- 반드시 JSON으로만 출력
- rating은 1~5 사이 정수
- pros 3개
- cons 3개

JSON 구조:
{{
    "title": "string",
    "rating": number,
    "pros": ["string", "string", "string"],
    "cons": ["string", "string", "string"],
    "summary": "string"
}}
"""


# ---------------------------------------------------
# 2. AI 호출 함수
# ---------------------------------------------------
def request_review_from_ai(review_prompt: str) -> str:
    """
    OpenAI API를 호출해서 결과를 받아오는 함수
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": review_prompt}
        ]
    )

    # AI가 생성한 텍스트 반환
    return response.choices[0].message.content


# ---------------------------------------------------
# 3. 응답 정제 함수
# ---------------------------------------------------
def sanitize_response_text(raw_response_text: str) -> str:
    """
    AI 응답에서 불필요한 Markdown 제거

    예:
    ```json
    {...}
    ```
    → {...}
    """

    sanitized_text = raw_response_text.strip()

    # ```json 제거
    if sanitized_text.startswith("```json"):
        sanitized_text = sanitized_text[len("```json"):].strip()

    # ``` 제거
    if sanitized_text.startswith("```"):
        sanitized_text = sanitized_text[len("```"):].strip()

    if sanitized_text.endswith("```"):
        sanitized_text = sanitized_text[:-3].strip()

    return sanitized_text


# ---------------------------------------------------
# 4. JSON 파싱
# ---------------------------------------------------
def parse_json_response(sanitized_text: str) -> dict:
    """
    문자열 → JSON 객체 변환
    """

    return json.loads(sanitized_text)


# ---------------------------------------------------
# 5. 검증 로직
# ---------------------------------------------------
def validate_review_json(review_data: dict) -> tuple[bool, list[str]]:
    """
    JSON 데이터가 조건을 만족하는지 검사

    반환:
    - True/False
    - 에러 목록
    """

    errors = []

    required_keys = ["title", "rating", "pros", "cons", "summary"]

    # 필수 키 검사
    for key in required_keys:
        if key not in review_data:
            errors.append(f"누락된 키: {key}")

    # rating 검사
    if "rating" in review_data:
        if not isinstance(review_data["rating"], int):
            errors.append("rating은 정수여야 합니다.")
        elif not (1 <= review_data["rating"] <= 5):
            errors.append("rating은 1~5 사이여야 합니다.")

    # pros 검사
    if "pros" in review_data:
        if not isinstance(review_data["pros"], list):
            errors.append("pros는 배열이어야 합니다.")
        elif len(review_data["pros"]) != 3:
            errors.append("pros는 3개여야 합니다.")

    # cons 검사
    if "cons" in review_data:
        if not isinstance(review_data["cons"], list):
            errors.append("cons는 배열이어야 합니다.")
        elif len(review_data["cons"]) != 3:
            errors.append("cons는 3개여야 합니다.")

    # 에러가 없으면 True
    return len(errors) == 0, errors


# ---------------------------------------------------
# 6. 전체 실행 함수 (핵심)
# ---------------------------------------------------
def generate_review(
    product_name: str,
    target_audience: str,
    review_tone: str,
    desired_rating: int = 4,
    max_retry_count: int = 3
) -> dict:
    """
    전체 흐름을 담당하는 핵심 함수

    기능:
    - 프롬프트 생성
    - AI 호출
    - 정제
    - 파싱
    - 검증
    - 실패 시 재시도
    """

    last_error = None

    # 프롬프트 생성
    review_prompt = build_review_prompt(
        product_name,
        target_audience,
        review_tone,
        desired_rating
    )

    # 재시도 루프
    for attempt in range(1, max_retry_count + 1):

        try:
            # 1. AI 호출
            raw_response_text = request_review_from_ai(review_prompt)

            # 2. 텍스트 정제
            sanitized_text = sanitize_response_text(raw_response_text)

            # 3. JSON 파싱
            review_data = parse_json_response(sanitized_text)

            # 4. 검증
            is_valid, errors = validate_review_json(review_data)

            # 성공
            if is_valid:
                return {
                    "success": True,
                    "attempt": attempt,
                    "prompt": review_prompt,
                    "raw_response": raw_response_text,
                    "sanitized_response": sanitized_text,
                    "review_data": review_data,
                    "errors": []
                }

            # 실패 기록
            last_error = {
                "type": "validation_error",
                "attempt": attempt,
                "errors": errors
            }

        except Exception as e:
            # 파싱 실패 등 예외 처리
            last_error = {
                "type": "exception",
                "attempt": attempt,
                "errors": [str(e)]
            }

    # 최종 실패 반환
    return {
        "success": False,
        "attempt": max_retry_count,
        "review_data": None,
        "errors": last_error["errors"] if last_error else ["알 수 없는 오류"]
    }