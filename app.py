import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import requests # 인터넷으로 데이터를 보내는 도구
import json

# 페이지 설정
st.set_page_config(page_title="대한제분 업무일지 (서버리스)", layout="wide")

# ==========================================
# 🔑 [중요] https://script.google.com/macros/s/AKfycbx_f-i0Se97bj3JzdYHQM8_UDf8PmyAndQl10BIhn-bH3Degfkgt5Zx7UoTUMQyCXX0/exec
# ==========================================
# 예시: "https://script.google.com/macros/s/xxxxxxxxx/exec"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbx_f-i0Se97bj3JzdYHQM8_UDf8PmyAndQl10BIhn-bH3Degfkgt5Zx7UoTUMQyCXX0/exec"

# 구글 시트 읽기용 URL (자동 생성됨 - 수정 X)
# 주의: 이 기능을 쓰려면 구글 시트에서 [파일] -> [공유] -> [웹에 게시] -> [게시]를 한번 해줘야 합니다.
# 그리고 그 시트의 ID(주소창의 /d/와 /edit 사이의 긴 문자열)를 아래에 넣어야 합니다.
SHEET_ID = "1qyeChG4aqAI1AgYikAAPFOzA2kkIXdMWzlJKlN_zncM" 
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"


# ==========================================
# 1. 데이터 전송 함수 (구글 시트로 쏘기)
# ==========================================
def send_to_google_sheet(date, name, w_type, cat, sub, hours):
    if "여기에" in WEB_APP_URL:
        return False, "🚨 코드 15번째 줄에 '웹 앱 URL'을 먼저 입력해주세요!"
    
    data = {
        "date": str(date),
        "name": name,
        "type": w_type,
        "category": cat,
        "subcategory": sub,
        "hours": hours
    }
    
    try:
        response = requests.post(WEB_APP_URL, json=data)
        if response.status_code == 200:
            return True, "저장 성공"
        else:
            return False, "전송 실패"
    except Exception as e:
        return False, f"에러 발생: {e}"

# ==========================================
# 2. 화면 구성 (기존 V1.2와 동일)
# ==========================================
TASK_STRUCTURE = {
    "🏢 조직 매니지먼트": ["사내회의", "문서작성", "교육/지도", "개인 검토", "기타"],
    "🔬 연구": ["실험·시제품 제작", "데이터 정리·문서 작성", "조사·검색", "특허·논문 관련", "사내외 회의", "기타"],
    "🚀 개발 (NPD 관련)": ["실험·시제품 제작", "데이터 정리·문서 작성", "조사·검색", "특허·논문 관련", "사내외 회의", "실수요·위탁처 연계", "기타"],
    "🛠️ 개발 (NPD 외)": ["실험·시제품 제작", "데이터 정리·문서 작성", "조사·검색", "특허·논문 관련", "사내외 회의", "실수요·위탁처 연계", "기타"],
    "🤝 영업 지원": ["실험 샘플 제작", "빵·면·과자 제품 테스트", "문서 작성", "VOC 관련 업무", "사내외 회의", "사용처 방문 동행", "기타"],
    "etc 기타": ["연구실 유지보수·안전관리", "타부서 업무 지원", "시장 조사·전시회 참관", "사내외 교육 수강", "강연·교육 담당", "사내외 회의", "기타(주관식 문항)"]
}

st.markdown("## 📝 대한제분 업무 종사표 (Auto-Save)")
st.caption("서버 없이 구글 시트에 자동 저장되는 버전입니다.")

col1, col2, col3 = st.columns(3)
with col1:
    user_name = st.text_input("이름", placeholder="홍길동")
with col2:
    work_date = st.date_input("날짜", datetime.now())
with col3:
    work_type = st.selectbox("근무 형태", ["정상 근무", "외근/출장", "반차/휴가"])

if not user_name:
    st.warning("이름을 입력해주세요.")
    st.stop()

st.divider()

# 입력 로직
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

# 제출 조건 확인
st.markdown("---")
submit_possible = False

if work_type == "정상 근무":
    if total_hours == 8:
        st.success("✅ 8시간 입력 완료")
        submit_possible = True
    else:
        st.error(f"⚠️ 정상 근무는 8시간을 채워야 합니다. (현재: {total_hours}시간)")
else:
    if 0 < total_hours <= 8:
        st.success(f"✅ {work_type} 입력 완료")
        submit_possible = True
    elif total_hours > 8:
        st.error("⚠️ 8시간 초과")

# ==========================================
# 3. 제출 버튼 (구글 시트로 전송)
# ==========================================
if st.button("🚀 제출 및 자동 저장", disabled=not submit_possible, use_container_width=True):
    success_count = 0
    with st.status("구글 시트로 데이터 전송 중...", expanded=True) as status:
        for (cat, sub, time) in inputs.values():
            st.write(f"📤 전송 중: {sub} ({time}시간)")
            is_ok, msg = send_to_google_sheet(work_date, user_name, work_type, cat, sub, time)
            if is_ok:
                success_count += 1
            else:
                st.error(f"실패: {msg}")
        
        if success_count > 0:
            status.update(label="✅ 저장 완료!", state="complete", expanded=False)
            st.balloons()
            st.toast(f"{success_count}건의 업무 기록이 구글 시트에 저장되었습니다.")
        else:
            status.update(label="❌ 저장 실패", state="error")

# ==========================================
# 4. 저장된 데이터 불러오기 (시각화)
# ==========================================
st.divider()
st.subheader("📊 실시간 저장 현황")

try:
    if "여기에" not in SHEET_ID:
        # 구글 시트 CSV 읽어오기 (별도 인증 필요 없음)
        df_log = pd.read_csv(CSV_URL)
        
        # 오늘 내 데이터만 필터링
        # (주의: 구글 시트 날짜 형식과 파이썬 날짜 형식이 일치해야 함. 여기서는 단순 표시용)
        st.dataframe(df_log.tail(10), use_container_width=True) # 최근 10개만 보여줌
        
        st.download_button("📥 전체 데이터 다운로드", df_log.to_csv().encode('utf-8-sig'), "backup.csv")
    else:
        st.info("데이터를 보려면 코드 상단에 SHEET_ID를 입력해야 합니다.")
except:
    st.caption("아직 데이터가 없거나 시트 연결(웹에 게시)이 안 되었습니다.")
