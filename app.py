import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 페이지 설정
st.set_page_config(page_title="대한제분 일일 업무일지 V1.2", layout="wide")

# ==========================================
# 0. 구글 시트 연동 설정 (저장 기능)
# ==========================================
def save_to_google_sheet(data_row):
    """구글 시트에 데이터를 한 줄 추가하는 함수"""
    try:
        # Streamlit Secrets에서 인증 정보 가져오기
        if "gcp_service_account" not in st.secrets:
            return False, "구글 시트 연동 설정이 없습니다. (CSV 다운로드 이용 요망)"

        # 인증 및 시트 연결
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # 시트 열기 (시트 이름: 'work_log_db') - 미리 만들어둬야 함
        sheet = client.open("work_log_db").sheet1
        sheet.append_row(data_row)
        return True, "구글 시트에 안전하게 저장되었습니다."
    except Exception as e:
        return False, f"구글 시트 저장 실패: {str(e)}"

# ==========================================
# 1. 데이터 구조 및 초기화
# ==========================================
TASK_STRUCTURE = {
    "🏢 조직 매니지먼트": ["사내회의", "문서작성", "교육/지도", "개인 검토", "기타"],
    "🔬 연구": ["실험·시제품 제작", "데이터 정리·문서 작성", "조사·검색", "특허·논문 관련", "사내외 회의", "기타"],
    "🚀 개발 (NPD 관련)": ["실험·시제품 제작", "데이터 정리·문서 작성", "조사·검색", "특허·논문 관련", "사내외 회의", "실수요·위탁처 연계", "기타"],
    "🛠️ 개발 (NPD 외)": ["실험·시제품 제작", "데이터 정리·문서 작성", "조사·검색", "특허·논문 관련", "사내외 회의", "실수요·위탁처 연계", "기타"],
    "🤝 영업 지원": ["실험 샘플 제작", "빵·면·과자 제품 테스트", "문서 작성", "VOC 관련 업무", "사내외 회의", "사용처 방문 동행", "기타"],
    "etc 기타": ["연구실 유지보수·안전관리", "타부서 업무 지원", "시장 조사·전시회 참관", "사내외 교육 수강", "강연·교육 담당", "사내외 회의", "기타(주관식 문항)"]
}

if 'work_logs' not in st.session_state:
    st.session_state.work_logs = pd.DataFrame(columns=["날짜", "이름", "근무형태", "대분류", "소분류", "시간"])

# ==========================================
# 2. 사용자 정보 및 근무 형태 (조건 설정)
# ==========================================
st.markdown("## 📝 일일 업무 종사 시간 입력표 (V1.2)")

col1, col2, col3 = st.columns(3)
with col1:
    user_name = st.text_input("이름 (필수)", placeholder="홍길동")
with col2:
    work_date = st.date_input("날짜 (필수)", datetime.now())
with col3:
    # 2. 근무 형태 탭 (외근/반차 선택)
    work_type = st.selectbox("근무 형태", ["정상 근무", "외근/출장", "반차/휴가"])

if not user_name:
    st.warning("👈 이름을 입력해야 업무 기록이 가능합니다.")
    st.stop()

st.divider()

# ==========================================
# 3. 업무 시간 입력 (입력 로직)
# ==========================================
inputs = {}
total_hours = 0
cols = st.columns(2)

for idx, (category, sub_tasks) in enumerate(TASK_STRUCTURE.items()):
    with cols[idx % 2]:
        with st.expander(f"**{category}**", expanded=False):
            for task in sub_tasks:
                key = f"{category}_{task}"
                val = st.number_input(f"{task}", min_value=0.0, max_value=8.0, step=0.5, key=key)
                if val > 0:
                    inputs[key] = (category, task, val)
                    total_hours += val

# ==========================================
# 4. 스마트 제출 검증 (1번, 2번 요구사항)
# ==========================================
st.markdown("---")
st.subheader("⏱️ 입력 현황 확인")

# 조건 검사 로직
submit_possible = False
msg = ""

if work_type == "정상 근무":
    if total_hours == 8:
        msg = "✅ 정상 근무 8시간이 정확히 입력되었습니다."
        submit_possible = True
        st.success(msg)
    else:
        msg = f"⚠️ 정상 근무는 **정확히 8시간**을 채워야 합니다. (현재: {total_hours}시간)"
        st.error(msg)
else: # 외근, 반차 등
    if 0 < total_hours <= 8:
        msg = f"✅ {work_type} 기준 입력이 완료되었습니다. (현재: {total_hours}시간)"
        submit_possible = True
        st.success(msg)
    elif total_hours > 8:
        msg = f"⚠️ 근무 시간은 8시간을 초과할 수 없습니다. (현재: {total_hours}시간)"
        st.error(msg)
    else:
        msg = "업무 시간을 입력해주세요."
        st.info(msg)

# 제출 버튼
if st.button("💾 업무일지 제출 및 저장", disabled=not submit_possible, use_container_width=True):
    # 1. 로컬 세션에 저장
    new_rows = []
    for (cat, sub, time) in inputs.values():
        row = [str(work_date), user_name, work_type, cat, sub, time]
        
        # 세션 저장용 (딕셔너리)
        new_rows.append({
            "날짜": str(work_date), "이름": user_name, "근무형태": work_type,
            "대분류": cat, "소분류": sub, "시간": time
        })
        
        # 4. 구글 시트 저장 시도 (저장 방식)
        success, log_msg = save_to_google_sheet(row)
    
    st.session_state.work_logs = pd.concat([st.session_state.work_logs, pd.DataFrame(new_rows)], ignore_index=True)
    
    if success:
        st.toast(log_msg, icon="☁️")
    else:
        st.toast("구글 시트 미연동 상태: 임시 저장만 완료되었습니다.", icon="📂")
    
    st.balloons()

# ==========================================
# 5. 시각화 (3번 요구사항 - Drill Down)
# ==========================================
if not st.session_state.work_logs.empty:
    st.divider()
    st.markdown("## 📊 내 업무 분석 (섹터를 클릭해보세요!)")
    
    # 현재 사용자의 오늘 데이터만 필터링
    my_data = st.session_state.work_logs[
        (st.session_state.work_logs['이름'] == user_name) & 
        (st.session_state.work_logs['날짜'] == str(work_date))
    ]
    
    if not my_data.empty:
        col_chart, col_detail = st.columns([1, 1])
        
        with col_chart:
            # 대분류 집계
            pie_data = my_data.groupby("대분류")['시간'].sum().reset_index()
            
            # Altair 인터랙티브 차트 (클릭 기능 추가)
            selection = alt.selection_point(fields=['대분류'])
            
            base = alt.Chart(pie_data).encode(
                theta=alt.Theta("시간", stack=True)
            )
            
            pie = base.mark_arc(outerRadius=120, innerRadius=60).encode(
                color=alt.Color("대분류"),
                order=alt.Order("시간", sort="descending"),
                opacity=alt.condition(selection, alt.value(1), alt.value(0.3)),
                tooltip=["대분류", "시간"]
            ).add_params(selection)
            
            text = base.mark_text(radius=140).encode(
                text=alt.Text("시간", format=".1f"),
                order=alt.Order("시간", sort="descending"),
                color=alt.value("black")  
            )
            
            # on_select="rerun"을 사용하여 클릭 시 재실행되도록 함 (최신 Streamlit 기능)
            chart_event = st.altair_chart(pie + text, use_container_width=True, on_select="rerun", selection_mode="point")

        with col_detail:
            st.markdown("### 📋 세부 내역")
            
            # 차트에서 선택된 값이 있는지 확인
            selected_sector = None
            if len(chart_event['selection']['point_selection_1']) > 0:
                 selected_sector = chart_event['selection']['point_selection_1'][0]['대분류']
            
            if selected_sector:
                st.info(f"**'{selected_sector}'**의 상세 업무 내역입니다.")
                detail_view = my_data[my_data['대분류'] == selected_sector][['소분류', '시간']]
                st.dataframe(detail_view, use_container_width=True, hide_index=True)
            else:
                st.caption("👈 왼쪽 원형 차트의 조각을 클릭하면 세부 내역이 여기에 나타납니다.")
                # 전체 내역 보여주기
                st.dataframe(my_data[['대분류', '소분류', '시간']], use_container_width=True, hide_index=True)

    # 엑셀 다운로드 (백업용)
    st.divider()
    csv = st.session_state.work_logs.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 전체 데이터 엑셀(CSV) 백업 다운로드", csv, "work_log_backup.csv")
