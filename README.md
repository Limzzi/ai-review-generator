# AI 제품 리뷰 생성기

프롬프트 엔지니어링 학습과 AI 웹앱 포트폴리오 제작을 위해 만든 Streamlit 기반 프로젝트입니다.

## 프로젝트 소개
사용자가 상품명, 타겟, 톤, 희망 평점을 입력하면 AI가 구조화된 제품 리뷰를 JSON 형식으로 생성합니다.

## 주요 기능
- 상품명 / 타겟 / 톤 입력 UI
- 희망 평점 슬라이더 UI
- 예시 입력 버튼
- AI 리뷰 생성
- JSON 정제 및 파싱
- 출력 검증
- 실패 시 재시도
- 결과 카드 형태 출력

## 사용 기술
- Python
- Streamlit
- OpenAI API
- python-dotenv

## 파일 구조
ai-review-generator/
├─ app.py
├─ review_generator.py
├─ .env
├─ .gitignore
├─ requirements.txt
└─ README.md

## 실행 방법
pip install -r requirements.txt
streamlit run app.py