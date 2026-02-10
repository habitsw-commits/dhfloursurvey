import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="대한제분 일일 업무일지", layout="wide")

# ==========================================
# 1. 초기 설정 및 데이터 구조 정의
# ==========================================

# 사진에 있는 업무 분류 체계 정의
TASK_STRUCTURE = {
    "🏢 조직 매니지먼트": ["사내회의", "문서작성", "교육/지도", "개인 검토", "기타"],
    "🔬 연구": ["실험·시제품 제작", "데이터 정리·문서 작성", "조사·검색", "특허·논문 관련", "사내외 회의", "기타"],
    "🚀 개발 (NPD 관련)": ["실험·시제품 제작", "데이터 정리·문서 작성", "조사·검색", "특허·논문 관련", "사내외 회의", "실수요·위탁처 연계", "기타"],
    "🛠️ 개발 (NPD 외)": ["실험·시제품 제작", "데이터 정리·문서 작성", "조사·검색", "특허·논문 관련", "사내외 회의", "실수요·위탁처 연계", "기타"],
    "🤝 영업 지원": ["실험 샘플 제작", "빵·면·과자 제품 테스트", "문서 작성", "VOC 관련 업무", "사내외 회의", "사용처 방문 동행", "기타"],
    "etc 기타": ["연구실 유지보수·안전관리", "타부서 업무 지원", "시장 조사·전시회 참관", "사내외 교육 수강", "강연·교육 담당", "사내외 회의", "기타(주관식 문항)"]
}

# 세션 상태 초기화 (데이터 임시 저장소)
if 'work_logs' not in st.session_state:
    st.session_state.work_logs = pd.DataFrame(columns=["날짜", "이름", "대분류", "소분류", "시간"])
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# ==========================================
# 2. 사용자 정보 입력 (필수)
# ==========================================
st.markdown("## 📝 일일 업무 종사 시간 입력표")
st.info("하루 총 근무 시간은 **8시간**을 초과할 수 없습니다.")

col1, col2 = st.columns(2)
with col1:
    user_name = st.text_input("이름 (필수)", placeholder="홍길동")
with col2:
    work_date = st.date_input("날짜 (필수)", datetime.now())

# 이름이 없으면 진행 불가
if not user_name:
    st.warning("👈 먼저 이름을 입력해주세요. (이름 입력 후 업무 기록 가능)")
    st.stop()

st.divider()

# ==========================================
# 3. 업무 시간 입력 (동적 계산)
# ==========================================

# 입력을 저장할 딕셔너리
inputs = {}
total_hours = 0

# 2열 레이아웃으로 입력폼 배치
cols = st.columns(2)

# 각 카테고리별로 입력창 생성
for idx, (category, sub_tasks) in enumerate(TASK_STRUCTURE.items()):
    with cols[idx % 2]: # 왼쪽, 오른쪽 번갈아가며 배치
        with st.expander(f"**{category}**", expanded=False):
            for task in sub_tasks:
                key = f"{category}_{task}"
                # 0~8시간 입력 (0.5시간 단위도 가능하게 하려면 step=0.5)
                val = st.number_input(f"{task}", min_value=0, max_value=8, step=1, key=key)
                if val > 0:
                    inputs[key] = (category, task, val)
                    total_hours += val

# ==========================================
# 4. 실시간 검증 및 제출
# ==========================================

# 화면 하단에 고정된 상태바 (총 시간 표시)
st.markdown("---")
st.subheader("⏱️ 입력 현황")

# 8시간 초과 여부 확인
if total_hours > 8:
    st.error(f"⚠️ 총 {total_hours}시간입니다! 8시간을 초과할 수 없습니다.")
    submit_disabled = True
elif total_hours == 0:
    st.caption("업무 시간을 입력해주세요.")
    submit_disabled = True
else:
    st.success(f"현재 총 {total_hours}시간 입력되었습니다. (제출 가능)")
    submit_disabled = False

# 제출 버튼
if st.button("✅ 업무일지 제출하기", disabled=submit_disabled, use_container_width=True):
    # 데이터 저장 로직
    new_logs = []
    for (cat, sub, time) in inputs.values():
        new_logs.append({
            "날짜": work_date,
            "이름": user_name,
            "대분류": cat,
            "소분류": sub,
            "시간": time
        })
    
    # 세션에 데이터 추가
    new_df = pd.DataFrame(new_logs)
    st.session_state.work_logs = pd.concat([st.session_state.work_logs, new_df], ignore_index=True)
    st.session_state.submitted = True # 제출 완료 플래그
    st.balloons() # 축하 효과

# ==========================================
# 5. 시각화 및 엑셀 다운로드 (제출 후 보임)
# ==========================================

if not st.session_state.work_logs.empty:
    st.divider()
    st.markdown("## 📊 업무 분석 리포트")
    
    # 1. 가장 최근 제출한 사람의 데이터만 필터링해서 차트 그리기
    current_data = st.session_state.work_logs[
        (st.session_state.work_logs['이름'] == user_name) & 
        (st.session_state.work_logs['날짜'] == pd.Timestamp(work_date))
    ]
    
    if not current_data.empty:
        # 대분류별 합계 계산
        chart_data = current_data.groupby("대분류")['시간'].sum().reset_index()
        
        # Altair 원형 차트 (도넛 모양)
        base = alt.Chart(chart_data).encode(
            theta=alt.Theta("시간", stack=True)
        )
        
        pie = base.mark_arc(outerRadius=120, innerRadius=60).encode(
            color=alt.Color("대분류"),
            order=alt.Order("시간", sort="descending"),
            tooltip=["대분류", "시간"]
        )
        
        text = base.mark_text(radius=140).encode(
            text=alt.Text("시간", format=".1f"),
            order=alt.Order("시간", sort="descending"),
            color=alt.value("black")
        )
        
        st.altair_chart(pie + text, use_container_width=True)
        
        # 상세 내역 (Expandable)
        with st.expander("📌 상세 세부 내역 확인하기"):
            st.dataframe(current_data[["대분류", "소분류", "시간"]], use_container_width=True)

    # 2. 전체 로그 다운로드 (엑셀)
    st.markdown("### 💾 데이터베이스 관리")
    st.write(f"총 누적 데이터: {len(st.session_state.work_logs)}건")
    
    # CSV 변환
    csv = st.session_state.work_logs.to_csv(index=False).encode('utf-8-sig')
    
    st.download_button(
        label="📥 전체 업무일지 엑셀 다운로드 (CSV)",
        data=csv,
        file_name=f"업무일지_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
        key='download-csv'
    )

    st.warning("주의: 이 페이지를 '새로고침'하면 누적된 데이터가 사라집니다. 퇴근 전 반드시 다운로드하세요!")
