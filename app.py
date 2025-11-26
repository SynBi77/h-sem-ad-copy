import streamlit as st
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="H-SEM AI Assistant", layout="wide")
st.title("🚀 H-SEM 검색 광고 카피 생성기")

# 2. API Key 설정 (Secrets에서 가져오기)
# 이 부분은 사용자가 입력하지 않고, 서버에 저장된 키를 자동으로 불러옵니다.
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("API Key가 설정되지 않았습니다. 관리자에게 문의하세요.")

# 3. 입력 및 실행 로직
user_input = st.text_area("요청 사항을 입력하세요.", height=150, placeholder="예: 아이오닉5 11월 프로모션 검색 광고 문구 5개 생성해줘")

if st.button("광고 카피 생성"):
    if not user_input:
        st.warning("내용을 입력해주세요.")
    else:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            with st.spinner("AI가 분석 및 생성 중입니다..."):
                response = model.generate_content(user_input)
            st.success("완료!")
            st.markdown("### 생성 결과")
            st.write(response.text)
        except Exception as e:
            st.error(f"에러 발생: {e}")
