import streamlit as st
st.set_page_config(
    page_title="세계 데이터 대시보드",
    page_icon=":bar_chart:",
    layout="wide"
)
st.title("세계 데이터 대시보드")
st.subheader("세계 데이터 시각화 및 분석을 위한 대시보드입니다.")
st.divider() # 여기부터 수정!!!!!!!!!!!!!!!!!!!!!!!!!!
import plotly.express as px
df = px.data.gapminder()

col1, col2, col3 = st.columns(3)
col1.metric("국가 수", df['country'].nunique())
col2.metric("연도 수", df['year'].nunique())
col3.metric("데이터 수", df.shape[0])
st.divider()
st.dataframe(df.head(10), use_container_width=True)


st.write("안녕하세요! 연습중!!!")
st.markdown("""
- **국가별 GDP, 기대수명, 인구데이터
- 1952년 ~ 2007년
- 142개국
""")
st.divider()
st.info('튜토리얼')
# 아나콘다 프롬프트에서 실행
# streamlit run 01_app.py