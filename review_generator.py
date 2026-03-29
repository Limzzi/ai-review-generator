import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

client = OpenAI(api_key=api_key)

def build_review_prompt(
    product_name: str,
    target_audience: str,
    review_tone: str,
    desired_rating: int
) -> str:
    return f"""
너는 전문적인 제품 리뷰어다.

목표:
주어진 상품에 대해 구조화된 리뷰를 작성하라.

조건:
- product: {product_name}
- target: {target_audience}
- tone: {review_tone}
- desired_rating: {desired_rating}
- target에 맞는 표현 사용
- tone에 맞는 자연스러운 문체 사용
- rating은 desired_rating에 가깝게 작성

출력 규칙:
- 반드시 JSON으로만 출력
- 불필요한 설명문 금지
- rating은 1~5 사이 정수
- pros 배열 길이는 반드시 3
- cons 배열 길이는 반드시 3

JSON 구조:
{{
    "title": "string",
    "rating": number,
    "pros": ["string", "string", "string"],
    "cons": ["string", "string", "string"],
    "summary": "string"
}}
"""

def request_review_from_ai(review_prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": review_prompt}
        ]
    )
    return response.choices[0].message.content

def sanitize_response_text(raw_response_text: str) -> str:
    sanitized_text = raw_response_text.strip()

    if sanitized_text.startswith("```json"):
        sanitized_text = sanitized_text[len("```json"):].strip()

    if sanitized_text.startswith("```"):
        sanitized_text = sanitized_text[len("```"):].strip()

    if sanitized_text.endswith("```"):
        sanitized_text = sanitized_text[:-3].strip()

    return sanitized_text

def parse_json_response(sanitized_text: str) -> dict:
    return json.loads(sanitized_text)

def validate_review_json(review_data: dict) -> tuple[bool, list[str]]:
    errors = []
    required_keys = ["title", "rating", "pros", "cons", "summary"]

    for key in required_keys:
        if key not in review_data:
            errors.append(f"누락된 키: {key}")

    if "rating" in review_data:
        if not isinstance(review_data["rating"], int):
            errors.append("rating은 정수여야 합니다.")
        elif not (1 <= review_data["rating"] <= 5):
            errors.append("rating은 1~5 사이여야 합니다.")

    if "pros" in review_data:
        if not isinstance(review_data["pros"], list):
            errors.append("pros는 배열이어야 합니다.")
        elif len(review_data["pros"]) != 3:
            errors.append("pros는 3개여야 합니다.")

    if "cons" in review_data:
        if not isinstance(review_data["cons"], list):
            errors.append("cons는 배열이어야 합니다.")
        elif len(review_data["cons"]) != 3:
            errors.append("cons는 3개여야 합니다.")

    return len(errors) == 0, errors


def generate_review(
    product_name: str,
    target_audience: str,
    review_tone: str,
    desired_rating: int = 4,
    max_retry_count: int = 3
) -> dict:
    last_error = None
    review_prompt = build_review_prompt(
        product_name,
        target_audience,
        review_tone,
        desired_rating
    )

    for attempt in range(1, max_retry_count + 1):
        try:
            raw_response_text = request_review_from_ai(review_prompt)
            sanitized_text = sanitize_response_text(raw_response_text)
            review_data = parse_json_response(sanitized_text)
            is_valid, errors = validate_review_json(review_data)

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

            last_error = {
                "type": "validation_error",
                "attempt": attempt,
                "errors": errors,
                "raw_response": raw_response_text,
                "sanitized_response": sanitized_text
            }

        except Exception as e:
            last_error = {
                "type": "exception",
                "attempt": attempt,
                "errors": [str(e)]
            }

    return {
        "success": False,
        "attempt": max_retry_count,
        "prompt": review_prompt,
        "raw_response": last_error.get("raw_response", "") if last_error else "",
        "sanitized_response": last_error.get("sanitized_response", "") if last_error else "",
        "review_data": None,
        "errors": last_error.get("errors", ["알 수 없는 오류"]) if last_error else ["알 수 없는 오류"]
    }