import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(layout="wide")
st.title("📦 일일 재고 현황판")

# 1. 데이터 입력 섹션 (보안 고려)
st.subheader("1. 데이터를 붙여넣으세요")
data_input = st.text_area("엑셀 데이터를 복사해서 여기에 붙여넣으세요 (탭 구분자 지원)", height=150)

# 2. 구조 그리기 (HTML/CSS 사용)
st.subheader("2. 재고 현황 시각화")

def draw_inventory(data_list):
    # CSS 설정: 7x2 사각형과 6x3 원 배치
    html_code = """
    <style>
        .container { position: relative; width: 800px; height: 350px; background: white; margin-top: 50px; }
        .grid-box { 
            display: grid; grid-template-columns: repeat(7, 100px); 
            grid-template-rows: repeat(2, 100px); border: 1px solid black;
        }
        .rect { border: 1px solid black; height: 100px; width: 100px; }
        .circle { 
            position: absolute; width: 70px; height: 70px; border: 1.5px solid black; 
            border-radius: 50%; background: white; display: flex; flex-direction: column;
            align-items: center; justify-content: center; font-size: 11px; font-weight: bold;
        }
    </style>
    <div class="container">
        <div class="grid-box">
            """ + "".join(['<div class="rect"></div>' for _ in range(14)]) + """
        </div>
    </div>
    """
    
    # 원 데이터 배치 (가로 6, 세로 3 = 총 18개)
    circles_html = ""
    for i in range(min(len(data_list), 18)):
        row = i // 6  # 0, 1, 2
        col = i % 6   # 0~5
        top = (row * 100) - 35 + 50 # 원의 위치 조정
        left = (col * 100) + 100 - 35
        
        name = data_list[i][0] if len(data_list[i]) > 0 else "N/A"
        val = data_list[i][1] if len(data_list[i]) > 1 else "0"
        code = data_list[i][2] if len(data_list[i]) > 2 else ""
        
        # 품목별 색상 구분 (예시: WASW는 파란색)
        color = "blue" if "WASW" in name else "orange" if "WCRS" in name else "brown"
        
        circles_html += f'''
        <div class="circle" style="top:{top}px; left:{left}px;">
            <div style="color:{color};">{name}</div>
            <div>{val}</div>
            <div style="color:gray; font-size:9px;">{code}</div>
        </div>
        '''
    
    return html_code.replace('</div>\n    </div>', circles_html + '</div>\n    </div>')

if data_input:
    # 텍스트 데이터를 리스트로 변환
    df = pd.read_csv(StringIO(data_input), sep='\t', header=None)
    data_list = df.values.tolist()
    st.write("입력 확인:", df)
    
    # 도면 출력
    st.components.v1.html(draw_inventory(data_list), height=500)
else:
    st.info("엑셀에서 데이터를 복사하여 위 칸에 붙여넣으면 현황판이 그려집니다.")