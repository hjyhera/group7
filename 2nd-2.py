import gzip
import pickle
import random
import streamlit as st
import numpy as np
import faiss
import requests
from openai import OpenAI
import base64
import json
import urllib.parse
from streamlit_chat import message as st_message

if 'expiry_date' not in st.session_state:
    st.session_state.expiry_date = 0
if 'score' not in st.session_state:
    st.session_state.score = 800
#st.session_state.visarule = ["E-9 비자로 변경하기 위해서는 조건 점수가 400점 이상이어야 합니다.", "E-7-4 비자로 변경하기 위해서는 조건 점수가 800점 이상이어야 합니다.", "점수 조건을 만족하지 못하거나 제외대상자에 해당할 경우, 비자 변경이 어렵습니다."]
if 'visarule' not in st.session_state:
    st.session_state.visarule = ""
    with open('visarule.pickle', 'rb') as f:
        st.session_state.visarule_data = pickle.load(f)
    st.session_state.visarule_titles = list(st.session_state.visarule_data.keys())
    st.session_state.visarule_titles = st.session_state.visarule_titles[:90]

st.session_state.read_consulting_result = []
if 'visacase' not in st.session_state:
    st.session_state.visacase = ""
if 'changevisa' not in st.session_state:
    st.session_state.changevisa  = 0

if 'result' not in st.session_state:
    st.session_state.result = False
    
#크롤링 데이터 st.session_state.read_consulting_result에 불러오기 
with open("crawling_data.pickle", "rb") as f:
    data = pickle.load(f)

#print(data.keys())
#print(data['중도 퇴사 후 근로소득 신고되지 않아 고용허가연장 안된 노동자 지원'])

for i in data.keys():
    cstContent, cstResult, cstLaw, cstEval = data[i]
    dict = {"title": i, "content": cstContent, "result": cstResult, "law": cstLaw, "evaluation": cstEval}
    st.session_state.read_consulting_result.append(dict)


def get_visarule_case(indices):
    # '외교(A-1)', '공무(A-2)', '협정(A-3)', ' 협정(A-3)자격 소지자의 체류자격외 활동 범위', '사증면제(B-1)', '관광통과(B-2)', '일시취재(C-1)', '단기방문(C-3)', '단기취업(C-4)', '문화예술(D-1)', '유학(D-2)', '외국인유학생 시간제 취업(아르바이트)', '산업연수(D-3)', '일반연수(D-4)', '취재(D-5)', '종 교(D-6)', '주 재(D-7)', '필수전문인력', '기업투자(D-8)', '개인 납세사실증명원', '무역경영(D-9)', '구직(D-10)', '교 수(E-1)', '회화지도(E-2)', '연 구(E-3)', '기술지도(E-4)', '전문직업(E-5)', '예술흥행(E-6)',
    #  '특정활동(E-7)', '계절근로(E-8)', '비전문취업(E-9)', '선원취업(E-10)', '방문동거(F-1)', '거 주(F-2)', 'F-2-8', '공익사업투자 외국인에 대한 거주(F-2-9) 체류자격 변경허가', '동반(F-3)', '영 주(F-5)', '결혼이민(F-6)', '기 타(G-1)', '1. 산재보상진행 불법체류자등에 대한 기타(G-1-1) 체류자격 변경허가', '관광취업(H-1)'
    #제목이 내용 보다 1단계 느림(적음), 제목 + 1 = 내용
    res = ""
    for i in indices[0]:
        if i in [10, 11, 14, 15, 16, 17, 18, 19, 22, 23, 24, 25, 30, 31, 32, 33, 34, 35, 36, 37, 76, 77, 78, 79, 83, 84, 85, 88]: 
            res += str(st.session_state.visarule_data[st.session_state.visarule_titles[i-1]]) + "\n"
        if i == 12 or i== 13: #협정(A-3), 협정(A-3)자격 소지자의 체류자격외 활동 범위
            res += str(st.session_state.visarule_data[st.session_state.visarule_titles[11]]) + "\n" + str(st.session_state.visarule_data[st.session_state.visarule_titles[12]]) + "\n"
        elif i == 20 or i == 21: #유학(D-2)
            res += str(st.session_state.visarule_data[st.session_state.visarule_titles[19]]) + "\n" + str(st.session_state.visarule_data[st.session_state.visarule_titles[20]]) + "\n"
        elif i == 26 or i == 27: #주 재(D-7)
            res += str(st.session_state.visarule_data[st.session_state.visarule_titles[25]]) + "\n" + str(st.session_state.visarule_data[st.session_state.visarule_titles[26]]) + "\n"
        elif i == 28 or i == 29: #기업투자(D-8), 개인 납세사실증명원
            res += str(st.session_state.visarule_data[st.session_state.visarule_titles[27]]) + "\n" + str(st.session_state.visarule_data[st.session_state.visarule_titles[28]]) + "\n"
        elif i >= 38 and i <= 75:  #특정활동(E-7)
            res += str(st.session_state.visarule_data[st.session_state.visarule_titles[37]]) + "\n" + str(st.session_state.visarule_data[st.session_state.visarule_titles[38]]) + "\n"
            if i >= 40 and i <= 75:
                res += str(st.session_state.visarule_data[st.session_state.visarule_titles[i-1]]) + "\n"
        elif i == 80 or i == 81 or i == 82: #거 주(F-2), F-2-8, 공익사업투자 외국인에 대한 거주(F-2-9) 체류자격 변경허가
            res += str(st.session_state.visarule_data[st.session_state.visarule_titles[79]]) + "\n" + str(st.session_state.visarule_data[st.session_state.visarule_titles[80]]) + "\n" + str(st.session_state.visarule_data[st.session_state.visarule_titles[81]]) + "\n"
        elif i == 86 or i == 87: #기 타(G-1), 1. 산재보상진행 불법체류자등에 대한 기타(G-1-1) 체류자격 변경허가
            res += str(st.session_state.visarule_data[st.session_state.visarule_titles[85]]) + "\n" + str(st.session_state.visarule_data[st.session_state.visarule_titles[86]]) + "\n"
    return res
#08/07에 발급, 일주일 후 만료
token = ""
token = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXJ2aWNlX3R5cGUiOiIxIiwic2NvcGUiOlsicmVhZCJdLCJzZXJ2aWNlX25vIjoiMDAwMDA0NDI0MDAyIiwiZXhwIjoxNzIzNjI0NTYzLCJhdXRob3JpdGllcyI6WyJJTlNVUkFOQ0UiLCJQVUJMSUMiLCJCQU5LIiwiRVRDIiwiU1RPQ0siLCJDQVJEIl0sImp0aSI6ImRlZGFkMzNjLWYwY2QtNGQ4OS04NDYwLWQwOWMzOWY2M2IwYyIsImNsaWVudF9pZCI6IjFmNmZjMjFkLWUxYjQtNGE4Yy1iMGIwLWRjYmQ1NTlkNzI5NyJ9.B-oxznVbVLh8IAJ8PhaWLJfMSb0qr18NZEt37HssCi3QFk7rTHYqCs4AOynhe_nSmL9oRTL6uHIRvAjVE4fOQVzypZN8BLAheTAiWjhNp7LuNjfGPUQibKN3dLAi4xW0kRm88w1bqRwSjtjRXk0gaV2OLAwkof6YYZ3Kmm10FTdRSy4Yf98MAbTyEo9MPOOzAm5n5f1QzrZrA57sddKb-foGbMBZk1OdL3GjkCOhk6zUKvjmVBM23fOnBIKuYPcZWB98IRhbIO_kI1ZXJePD1zTlBQKH9FxKy2yLvXO8to3AAgAsGEZTXgpIp_DWp6wXwwWAKlCL0O919IX_lF8Vlw'
#api 호출을 원하면 token의 주석을 해제하고 사용하세요
def get_stay_expiration_date(passport_no, nationality, birth_date, token, country=None):
    url = "https://development.codef.io/v1/kr/public/mj/hi-korea/stay-expiration-date"  # 데모 버전 URL
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token  # 유효한 액세스 토큰을 입력하세요
    }
    data = {
        "organization": "0001",
        "passportNo": passport_no,
        "nationality": nationality,
        "birthDate": birth_date
    }
    if nationality == "99" and country:
        data["country"] = country

    response = requests.post(url, headers=headers, data=json.dumps(data), timeout=100)

    # 응답 본문 출력
    # st.write(f"Response Status Code: {response.status_code}")
    # st.write(f"Response Body: {response.text}")

    if response.status_code == 200:
        try:
            # URL 디코딩
            decoded_response = urllib.parse.unquote(response.text)
            # JSON 파싱
            return json.loads(decoded_response)
        except json.JSONDecodeError:
            st.write("Error: Response is not in JSON format")
            return None
    else:
        st.write(f"Error: {response.status_code} - {response.text}")
        return None
    
# Set pate config
st.set_page_config(
    page_title="Foreign Worker Chatbot Consultation",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Show title and description.
st.title("🤖 Foreign Worker Chatbot Consultation")
st.write("Welcome to the friendly chatbot consultation service for foreign workers. ")
st.write("Let's get started with some basic information.")


st.markdown(
    """
    
    <style>
        .main {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Arial', sans-serif;
        }
        div[data-baseweb="input"] {
            background-color: #ffffff;  /* 배경 색상 */
            border: 2px solid #6E6E6E;  /* 테두리 색상 */
            border-radius: 5px;  /* 모서리 둥글게 */
            padding: 0px;  /* 패딩 */
        }a
        .message-container {
            overflow: auto;
        }
        button[kind="primary"] {
        background-color: #81BEF7;
        border: #81BEF7;
        }
    </style>
    """,
    unsafe_allow_html=True
)


#flag = 시나리오 단계
if "flag" not in st.session_state:
    st.session_state.flag = "1"

openai_api_key = st.text_input("Enter OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:

    st.session_state.country = st.text_input("Enter your country.")

    if st.session_state.country:
        def translate(msg):
            client = OpenAI(api_key=openai_api_key)
            message = "Translate the following ';'-separated list " + msg + " into " + st.session_state.country + "'s language and only tell me that translation. Provide the translation as a ';'-separated list. If there isn't any ';', then you don't have to split it into ';'" 
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "assistant", "content": message}
                ],
            )
            return response.choices[0].message.content.strip()
        


        if 'translations' not in st.session_state:
            st.session_state.translations = {}
            st.session_state.translations['nationality_translation'] = translate("0:러시아;1:몽골;2:미국;3:베트남;4:인도;5:인도네시아;6:일본;7:중국;8:태국;9:필리핀;10:한국계 러시아인;11:한국계 중국인;99:기타;국적;상담결과보기;다시 채팅하기")
            st.session_state.translations['button'] = translate("상담 결과보기; 다시 채팅하기; 비자 점수 측정하기; 조회 중...; 당신은 현재 체류중인 외국인이 아닙니다.; 모든 정보를 입력해주세요.;제출; 점수")
            st.session_state.button = st.session_state.translations['button'].split(";")

        def get_passport_expiry(info):
            if token:
                response = get_stay_expiration_date(info["passportNo"], info["nationality"], info["birthDate"], token, info.get("country"))
                return response.get('data',{}).get('resExpirationDate',None)
            else:
                st.write("Token is not available.")

        def query_passport_expiry():
            st.subheader(st.session_state.translations['subheader'])
            st.session_state.passport_no = ""
            st.session_state.nationality = ""
            st.session_state.country_detail = ""
            st.session_state.birth_date = ""
            # 여권 번호
            st.session_state.passport_no = st.text_input('🛂'+ st.session_state.translations['passport_no'])

            # 국적
            nationality_translation = st.session_state.translations['nationality_translation']
            nationality_translation = nationality_translation.split(";")
            # 국적
            if nationality := st.selectbox('🌏'+nationality_translation[13], [
                nationality_translation[0], nationality_translation[1],
                nationality_translation[2], nationality_translation[3],
                nationality_translation[4], nationality_translation[5],
                nationality_translation[6], nationality_translation[7],
                nationality_translation[8], nationality_translation[9],
                nationality_translation[10],
                nationality_translation[11], nationality_translation[12]],
                index=None):
                if nationality == nationality_translation[0]:
                    st.session_state.nationality = "0"
                elif nationality == nationality_translation[1]:
                    st.session_state.nationality = "1"
                elif nationality == nationality_translation[2]:
                    st.session_state.nationality = "2"
                elif nationality == nationality_translation[3]:
                    st.session_state.nationality = "3"
                elif nationality == nationality_translation[4]:
                    st.session_state.nationality = "4"
                elif nationality == nationality_translation[5]:
                    st.session_state.nationality = "5"
                elif nationality == nationality_translation[6]:
                    st.session_state.nationality = "6"
                elif nationality == nationality_translation[7]:
                    st.session_state.nationality = "7"
                elif nationality == nationality_translation[8]:
                    st.session_state.nationality = "8"
                elif nationality == nationality_translation[9]:
                    st.session_state.nationality = "9"
                elif nationality == nationality_translation[10]:
                    st.session_state.nationality = "10"
                elif nationality == nationality_translation[11]:
                    st.session_state.nationality = "11"
                elif nationality == nationality_translation[12]:
                    st.session_state.country_detail = st.text_input('🏞️'+ st.session_state.translations['country_detail'])
            
        # 생년월일
            str = st.date_input('🎂'+ st.session_state.translations['birth_date'])
            st.session_state.birth_date =str.strftime('%Y%m%d')
            
            # 조회
            if st.button(st.session_state.translations['expire']):
                with st.spinner(st.session_state.button[3]):
                    if st.session_state.passport_no and st.session_state.nationality and st.session_state.birth_date:
                        info = {
                            "organization": "0001",
                            "passportNo": st.session_state.passport_no,
                            "nationality": st.session_state.nationality.split(":")[0],
                            "country": st.session_state.country_detail if st.session_state.nationality == nationality_translation[12] else "",
                            "birthDate": st.session_state.birth_date,
                        }
                        expiry_date = get_passport_expiry(info)
                        if expiry_date:
                            st.success(translate(f"체류만료일: {expiry_date}"))
                            st.session_state.expiry_date = expiry_date
                        else:
                            st.error(st.session_state.button[4])
                    else:
                        st.error(st.session_state.button[5])


        def user_info():
            if 'visa' not in st.session_state:
                st.session_state.visa = ""
            if 'visa_info' not in st.session_state:
                st.session_state.visa_info = ""
            if 'period' not in st.session_state:
                st.session_state.period = ""
            if 'purpose' not in st.session_state:
                st.session_state.purpose = ""
            if 'work' not in st.session_state:
                st.session_state.work = ""
            if 'init2' not in st.session_state:
                st.session_state.init2 = 1
                user_info_translation = translate("현재 비자가 있나요?;있음;없음; 현재 비자는 무엇입니까?;체류만료일을 조회하세요!;체류만료일 조회;한국 방문 목적을 입력하세요!;희망하는 직업/분야를 입력하세요!;여권 번호;국적;나라명;생년월일;정보를 입력하세요:")
                user_info_translation = user_info_translation.split(";")
                st.session_state.translations['visa'] = user_info_translation[0]
                st.session_state.translations['yes'] = user_info_translation[1]
                st.session_state.translations['no'] = user_info_translation[2]
                st.session_state.translations['visa_info'] = user_info_translation[3]
                st.session_state.translations['period'] = user_info_translation[4]
                st.session_state.translations['expire'] = user_info_translation[5]
                st.session_state.translations['purpose'] = user_info_translation[6]
                st.session_state.translations['work'] = user_info_translation[7]
                st.session_state.translations['passport_no'] = user_info_translation[8]
                st.session_state.translations['nationality'] = user_info_translation[9]
                st.session_state.translations['country_detail'] = user_info_translation[10]
                st.session_state.translations['birth_date'] = user_info_translation[11]
                st.session_state.translations['subheader'] = user_info_translation[12]

            # 비자 유무
            st.session_state.visa = st.radio('📌'+ st.session_state.translations['visa'],[st.session_state.translations['yes'],st.session_state.translations['no']], index=None)
            st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
            if st.session_state.visa == st.session_state.translations['yes']:
                # 있다면 현재 비자
                st.session_state.visa_info = st.text_input('📌'+ st.session_state.translations['visa_info'])
          
                              
            # 체류 기간
            st.session_state.period = st.write('📌'+ st.session_state.translations['period'])
            query_passport_expiry()

            # 한국 방문 목적       
            st.session_state.purpose = st.text_input('📌'+ st.session_state.translations['purpose'])
            
            # 직업/분야
            st.session_state.work = st.text_input('📌'+ st.session_state.translations['work'] )
            if st.session_state.work:
                done = st.button('Done')
                if done:
                    st.session_state.flag = "2"
                    st.rerun()

        def not_available(msg):
            client = OpenAI(api_key=openai_api_key)
            scenario_exclude = "E-7-4(e74) VISA의 제외대상: 벌금 100만원 이상의 형을 받은 자, 조세 체납자(완납 시 신청 가능), 출입국관리법 4회 이상 위반자, \
                불법체류 경력자, 대한민국의 이익이나 공공의 안전 등을 해치는 행동을 할 염려가 있다고 인정할 만한 자, 경제질서 또는 사회질서를 해치거나 선량한 풍속 등을 해치는 행동을 할 염려가 있다고 인정할 만한 자"
            
            message = "Please output '0' if assistant didn't guide user about the exclusion criteria.Please output '1' if assistant guided user about the exclusion criteria and user answered that he/she is excluded. Please output '2' if assistant guided user about the exclusion criteria and user answered that he/she is not excluded. Exclusion criteria:" + scenario_exclude
            data = "\nassistant와 user의 대화 데이터: "+ str(msg)
            response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": message + data}] + [
                    ],
                )
            if response.choices[0].message.content == "0":
                return
            elif response.choices[0].message.content == "1":
                st.session_state.subject = False
                st.session_state.flag = "5"
            elif response.choices[0].message.content == "2":
                st.session_state.subject = True
                st.session_state.flag = "4"
            return


        def get_score():
            st.session_state.score = 0
            if "messages" not in st.session_state:
                st.session_state.messages = []
            if 'init' not in st.session_state:
                st.session_state.init = 1
                get_score_translation = translate("최근 2년 간의 연간 평균 소득을 선택해주세요(2년 간의 총 소득 / 2);한국어 능력 자격증(TOPIK/KIIP/사전평가) 급수를 선택해주세요;나이를 선택해주세요;가점에 해당되는 요소가 있다면 입력해주세요;중앙부처 추천;광역지자체 추천;고용기업 추천;현 근무처 3년 이상 근속;인구감소 지역 및 읍면 지역 3년 이상 근무;자격증 또는 국내 학위;국내 면허;감점에 해당되는 요소가 있다면 입력해주세요;벌금 100만원 미만의 형을 받은 자;체납으로 체류허가 제한을 받은 사실이 있는 자;출입국관리법 3회 이하 위반자로 행정처분을 받은 자")
                get_score_translation = get_score_translation.split(";")
                st.session_state.translations['income'] = get_score_translation[0]
                st.session_state.translations['korean_ability'] = get_score_translation[1]
                st.session_state.translations['age'] = get_score_translation[2]
                st.session_state.translations['points'] = get_score_translation[3]
                st.session_state.translations['central_recommendation'] = get_score_translation[4]
                st.session_state.translations['local_government_recommendation'] = get_score_translation[5]
                st.session_state.translations['employment_recommendation'] = get_score_translation[6]
                st.session_state.translations['current_work'] = get_score_translation[7]
                st.session_state.translations['depopulation_area'] = get_score_translation[8]
                st.session_state.translations['certificate_or_degree'] = get_score_translation[9]
                st.session_state.translations['domestic_license'] = get_score_translation[10]
                st.session_state.translations['penalty'] = get_score_translation[11]
                st.session_state.translations['fine'] = get_score_translation[12]
                st.session_state.translations['restricted_permit'] = get_score_translation[13]
                st.session_state.translations['immigration_violation'] = get_score_translation[14]

            # 소득수준
            msg = st.session_state.translations['income'] 
            with st.chat_message("assistant", avatar="https://img.icons8.com/emoji/48/face-with-monocle.png"):
                st.markdown(msg)     
            income = st.radio(
                "",
                ["0~2500만원", "2500~3499만원", "3500~4999만원", "5000만원 이상"],
                label_visibility = "collapsed",
                index = None
            )
            if income == "0~2500만원":
                st.session_state.score += 0
            elif income == "2500~3499만원":
                st.session_state.score += 50
            elif income == "3500~4999만원":
                st.session_state.score += 80
            elif income == "5000만원 이상":
                st.session_state.score += 120

            # 한국어 능력
            msg = st.session_state.translations['korean_ability']
            with st.chat_message("assistant", avatar="https://img.icons8.com/emoji/48/face-with-monocle.png"):
                st.markdown(msg)       
            korean_ability = st.radio(
                "",
                ["X", "2급/2단계/41~60점", "3급/3단계/61~80점", "4급/4단계/81점~100점"],
                label_visibility = "collapsed",
                index = None
            )
            if korean_ability == "X":
                st.session_state.score += 0
            elif korean_ability == "2급/2단계/41~60점":
                st.session_state.score += 50
            elif korean_ability == "3급/3단계/61~80점":
                st.session_state.score += 80
            elif korean_ability == "4급/4단계/81점~100점":
                st.session_state.score += 120

            # 나이
            msg = st.session_state.translations['age']
            with st.chat_message("assistant", avatar="https://img.icons8.com/emoji/48/face-with-monocle.png"):
                st.markdown(msg)
            age = st.radio(
                " ",
                ["0~19세", "19세~26세", "27세~33세", "34세~40세", "41세~"],
                label_visibility = "collapsed",
                index = None
            )
            if age == "0~19세":
                st.session_state.score += 0
            elif age == "19세~26세":
                st.session_state.score += 40
            elif age == "27세~33세":
                st.session_state.score += 60
            elif age == "34세~40세":
                st.session_state.score += 30
            elif age == "41세~":
                st.session_state.score += 10

            # 가점
            msg = st.session_state.translations['points']
            with st.chat_message("assistant", avatar="https://img.icons8.com/emoji/48/face-with-monocle.png"):
                st.markdown(msg)

            plus1 = st.checkbox(st.session_state.translations['central_recommendation'])
            if plus1:
                st.session_state.score += 30

            plus2 = st.checkbox(st.session_state.translations['local_government_recommendation'])
            if plus2:
                st.session_state.score += 30

            plus3 = st.checkbox(st.session_state.translations['employment_recommendation'])
            if plus3:
                st.session_state.score += 50

            plus4 = st.checkbox(st.session_state.translations['current_work'])
            if plus4:
                st.session_state.score += 20

            plus5 = st.checkbox(st.session_state.translations['depopulation_area'])
            if plus5:
                st.session_state.score += 20

            plus6 = st.checkbox(st.session_state.translations['certificate_or_degree'])
            if plus6:
                st.session_state.score += 20

            plus7 = st.checkbox(st.session_state.translations['domestic_license'])
            if plus7:
                st.session_state.score += 10

            # 감점
            msg = st.session_state.translations['penalty']
            with st.chat_message("assistant", avatar="https://img.icons8.com/emoji/48/face-with-monocle.png"):
                st.markdown(msg)

            minus1 = st.checkbox(st.session_state.translations['fine'],key="minus1")
            if minus1:
                minus1_num = st.radio(
                "",
                ["1회", "2회", "3회 ~ "],
                label_visibility = "collapsed"
                )
                if minus1_num == "1회":
                    st.session_state.score -= 5
                elif minus1_num == "2회":
                    st.session_state.score -= 10
                elif minus1_num == "3회 ~ ":
                    st.session_state.score -= 20

            minus2 = st.checkbox(st.session_state.translations['restricted_permit'],key="minus2")
            if minus2:
                minus2_num = st.radio(
                " ",
                ["1회", "2회", "3회 ~ "],
                label_visibility = "collapsed"
                )
                if minus2_num == "1회":
                    st.session_state.score -= 5
                elif minus2_num == "2회":
                    st.session_state.score -= 10
                elif minus2_num == "3회 ~ ":
                    st.session_state.score -= 15

            minus3 = st.checkbox(st.session_state.translations['immigration_violation'],key="minus3")
            if minus3:
                minus3_num = st.radio(
                "  ",
                ["1회", "2회", "3회 ~ "],
                label_visibility = "collapsed"
                )
                if minus3_num == "1회":
                    st.session_state.score -= 5
                elif minus3_num == "2회":
                    st.session_state.score -= 10
                elif minus3_num == "3회 ~ ":
                    st.session_state.score -= 15

            submitted = st.button(st.session_state.button[6], type = "primary")
            if submitted:                  
                with st.chat_message("assistant", avatar="https://img.icons8.com/emoji/48/hushed-face.png"):
                    st.markdown(st.session_state.button[7]+ str(st.session_state.score))
                st.session_state.flag = "3"
                st.session_state.result = st.button(st.session_state.button[0], type = "primary")
                if st.session_state.result:
                    st.rerun()
                return st.session_state.score

        def check_response(msg):
            client = OpenAI(api_key=openai_api_key)
            check_sys = "당신은 외국인 근로자 상담사입니다. 서비스 이용 목적이 비자연장과 비자변경 중에 무엇인지 파악해야합니다. 사용자의 목적이 비자 연장이라고 판단되면 'extend'을 출력하고, 비자 변경이라면 'change'을 출력하세요"
            response_check = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": check_sys +  "사용자의 현재 비자:"+st.session_state.visa_info + "사용자의 사용 언어:"+st.session_state.country}] +
                    [{"role": "user", "content": msg}
                ],
                stream=False,
            )
            response_check_msg = response_check.choices[0].message.content
            return response_check_msg

        def get_embedding(input):
            client = OpenAI(api_key=openai_api_key)
            reponse = client.embeddings.create(
                input = input,
                model = "text-embedding-3-small"
            )
            embeddings = [data.embedding for data in reponse.data]
            return embeddings    
        


        def get_purpose():
            client = OpenAI(api_key=openai_api_key)
            st.session_state.subjectcase = f"국가: {st.session_state.country}, 현재 비자: {st.session_state.visa_info}, 변경을 원하는 비자: {st.session_state.visacase}, 체류 만료일: {st.session_state.expiry_date}, 한국 방문 목적: {st.session_state.purpose}, 업종: {st.session_state.work}"

            #system 프롬프트 설정
            scenario_purpose_sys = f"당신은 외국인 근로자 상담사입니다. user은 한국에서 일하고 있는 근로자이며, 당신에게 한국에서 일하면서 필요한 정보들을 물어보고자 합니다. 사용자 정보 {st.session_state.subjectcase}를 참고해서 사용자의 국가의 언어로 친절하게 대답해주세요"
            scenario_purpose_change = "The user wants to change his/her visa. First, you need to find out the type of visa the user wants to change by asking questions. Once you have found out, tell him/her the exclusion conditions for the visa he/she wants to change and ask him/her if he/she is excluded. Ask user to answer whether user is excluded or not"
            scenario_purpose_extend = "사용자가 비자의 연장을 원하고 있습니다. 연장하고자 하는 비자의 종류와 그 방법을 출력하세요."
            scenario_exclude = "You can find the exclusion conditions and the description for the visa that user want to change in here:" + st.session_state.visarule + "\nE-7-4(e74) VISA의 제외대상: 벌금 100만원 이상의 형을 받은 자, 조세 체납자(완납 시 신청 가능), 출입국관리법 4회 이상 위반자, \
                불법체류 경력자, 대한민국의 이익이나 공공의 안전 등을 해치는 행동을 할 염려가 있다고 인정할 만한 자, 경제질서 또는 사회질서를 해치거나 선량한 풍속 등을 해치는 행동을 할 염려가 있다고 인정할 만한 자.\n"

            if "messages" not in st.session_state:
                st.session_state.messages = []
            if 'get_purpose' not in st.session_state.translations:
                st.session_state.translations['get_purpose'] = translate("Please enter the purpose of using the service below.")

                msg = st.session_state.translations['get_purpose']
                bot_avatar_html = f'''
                <div style="text-align: left;">
                    <img src="https://img.icons8.com/emoji/48/smiling-face.png" width="50"/>
                </div>
                '''
                st.markdown(bot_avatar_html, unsafe_allow_html=True)
                st_message(msg, avatar_style="no-avatar")

            # Display the existing chat messages via `st.chat_message`.
            for message in st.session_state.messages:
                if message["role"] == "user":
                    user_avatar_html = f'''
                    <div style="text-align: right;">
                        <img src="https://img.icons8.com/emoji/48/thinking-face.png" width="50"/>
                    </div>
                    '''
                    st.markdown(user_avatar_html, unsafe_allow_html=True)
                    st_message(message["content"],is_user= True, avatar_style="no-avatar") 

                elif message["role"] == "assistant":
                    bot_avatar_html = f'''
                    <div style="text-align: left;">
                        <img src="https://img.icons8.com/emoji/48/smiling-face.png" width="50"/>
                    </div>
                    '''
                    st.markdown(bot_avatar_html, unsafe_allow_html=True)
                    st_message(message["content"], avatar_style="no-avatar") 
            
            if 'init3' not in st.session_state:
                st.session_state.init3 = 1
                st.session_state.messages.append({"role": "assistant", "content":msg})
            
            if "system_content" not in st.session_state:
                st.session_state.system_content = scenario_purpose_sys
        

            if prompt := st.chat_input(""):
                # Store and display the current prompt.
                st.session_state.messages.append({"role": "user", "content": prompt})
                user_avatar_html = f'''
                <div style="text-align: right;">
                    <img src="https://img.icons8.com/emoji/48/thinking-face.png" width="50"/>
                </div>
                '''
                st.markdown(user_avatar_html, unsafe_allow_html=True)
                st_message(prompt, is_user=True, avatar_style="no-avatar") 

                not_available(st.session_state.messages)
                if st.session_state.flag == "4" or st.session_state.flag == "5":
                    return

                #visa 변경 혹은 연장인지 확인
                response = check_response(prompt)
                if st.session_state.changevisa == 1:
                    st.session_state.visacase = prompt
                    #visa_rule 임배딩
                    db_vectors = []
                    db_vectors = np.array(get_embedding(st.session_state.visarule_titles))
                    query1 = np.array(get_embedding(st.session_state.visa_info))
                    query2 = np.array(get_embedding(st.session_state.visacase))
                    
                    d = db_vectors.shape[1]
                    index = faiss.IndexFlatL2(d)
                    index.add(db_vectors)
                    
                    k = 3
                    distances, indices = index.search(query1,k)
                    st.session_state.visarule = get_visarule_case(indices)
                    distances, indices = index.search(query2,k)
                    st.session_state.visacase += get_visarule_case(indices)
                    st.session_state.changevisa  = 0
                #확인 후 대처
                if response == "extend":
                    st.session_state.system_content = scenario_purpose_extend
                elif response == "change":
                    st.session_state.system_content = scenario_purpose_change + scenario_exclude
                    st.session_state.changevisa = 1
                else:
                    st.session_state.system_content = scenario_purpose_sys

                #목적에 맞춰서 질문을 생성
                answer = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                {"role": "system", "content": st.session_state.system_content+"사용자의 현재 비자:"+ st.session_state.visa_info + "사용자의 사용 언어:"+st.session_state.country}] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
                ],
                stream=False,
                )

                #답변생성   
                bot_avatar_html = f'''
                <div style="text-align: left;">
                    <img src="https://img.icons8.com/emoji/48/smiling-face.png" width="50"/>
                </div>
                '''
                st.markdown(bot_avatar_html, unsafe_allow_html=True)
                st_message(answer.choices[0].message.content, avatar_style="no-avatar")
                st.session_state.messages.append({"role": "assistant", "content": answer.choices[0].message.content})


                

        def get_answer():
            client = OpenAI(api_key=openai_api_key)
            
            qualifypoint = False
            assistant_data =""
            
            #점수 기준을 만족하는지의 여부 변수로 설정(get_score함수->score 점수 값으로 변경)
            if st.session_state.score >= 200 and st.session_state.score <= 800 :
                st.session_state.score_b = '1'
            elif st.session_state.score < 200:
                st.session_state.score_b = '2'
            else:
                st.session_state.score_b = '0'
            
            
            #피상담자의 상황(국가, 현재 비자, 체류 기간, 업종)
            st.session_state.subjectcase = f"국가: {st.session_state.country}, 현재 비자: {st.session_state.visa_info}, 변경을 원하는 비자: {st.session_state.visacase}, 체류 만료일: {st.session_state.expiry_date}, 한국 방문 목적: {st.session_state.purpose}업종: {st.session_state.work}"
            assistant_data = ""
            
            #제외대상자도 아니고, 점수 요건을 만족하는 경우, 
            if st.session_state.subject and st.session_state.score_b == '1':
                qualifypoint = True
                visarule_data = f"I will tell you the current conditions and circumstances of the user and the Korea's policy related to the visa that the user wants to change. \
                                The processing manual for the visa that needs to be changed is {st.session_state.visarule}. Can you tell me what documents the user need to prepare now?"
                
            #제외 대상자이거나, 점수 요건을 만족하지 못하는 경우, 
            #상담사례가 크롤링 처리되어 왔다고 가정(read_consulting 함수, 리턴값:딕셔너리 리스트{content:, result:}) 후 임배딩, 피상담자의 상황 역시 query 임배딩(2번 프로그램에서 받은 변경하고자 하는 비자 또는 추천받은 비자) 
            else:
                if st.session_state.subject == False:
                    assistant_data = "User is currently excluded from visa change and cannot change his/her visa. You must tell this one to user."
                    st.session_state.subjectcase += ", 제외 대상자: 해당"
                if st.session_state.score_b == '2':
                    assistant_data = "User cannot change his/her visa because he/she does not meet the visa point requirement. This must be printed."
                    st.session_state.subjectcase += ", 점수 기준 미달 여부: 해당"
                    
                #consulting = read_consulting()
                consulting = st.session_state.read_consulting_result
                db_vectors = []
                for each_data in consulting:
                    #임베딩 과정에 문제 상황과 답변을 다 포함시키기 위한 case 변수
                    consulting_case = f"상담 제목: {each_data['title']}, 상담 내용: {each_data['content']}, 상담 결과: {each_data['result']}, 관련 법령: {each_data['law']}, 평가 및 의의: {each_data['evaluation']}"
                    st.consulting_list = []
                    st.consulting_list.append(consulting_case)
                    #consulting 값을 딕셔너리와 임베딩 벡터가 모두 포함된 리스트로 변경
                db_vectors = np.array(get_embedding(st.consulting_list))

                query = np.array(get_embedding(st.session_state.subjectcase))
                
            
                d = db_vectors.shape[1]
                index = faiss.IndexFlatL2(d)
                index.add(db_vectors)
                
                k = 3
                distances, indices = index.search(query,k)
                indices_list = indices[0].tolist()
                
                
                #    #상위 3개의 상담사례 content를 가져와서 프롬프팅하고 싶은데 어떻게 해야할지?
                #    assistant_data = assistant_data + "지금 이 사람의 상황과 가장 유사한 3개의 상담사례를 가져왔어. 이 사례를 소개하고, 이 사람이 준비해볼만한 다른 비자를 알려주거나, 시도해볼만한 다른 방법을 알려줘"
                
                assistant_data += "사용자의 상황과 가장 유사한 3개의 상담사례를 가져왔습니다. 이 사례를 소개하고, 이 사람이 준비해볼만한 다른 비자를 알려주거나, 시도해볼만한 다른 방법을 알려주세요. 사례를 소개할 때 현재 상담자의 상황과 어떤 점이 비슷했는지도 설명해주세요."
                for i in indices_list:
                    case = consulting[i]
                    assistant_data += f"상담사례 {i+1}: 상담 제목 - {each_data['title']}, 상담 내용 - {each_data['content']}, 상담 결과 - {each_data['result']}, 관련 법령 - {each_data['law']}, 평가 및 의의 - {each_data['evaluation']} "

            language_message = f"지금부터 출력하는 언어는 반드시 모두 {st.session_state.country}의 언어로 출력해줘."                
            system_message = "You are a foreign job counselor working in Korea. The user is a foreigner who came to you for consultation. \
                                You have to perform a consultation scenario with the user. The consultation response should start with whether the foreigner can change the desired visa under the current conditions and circumstances. " 
            
            
            bot_avatar_html = f'''
                <div style="text-align: left;">
                    <img src="https://img.icons8.com/emoji/48/smiling-face.png" width="50"/>
                </div>
                '''
            st.markdown(bot_avatar_html, unsafe_allow_html=True)
            
            #기본 상담
            stream1 = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": language_message},
                    {"role": "system", "content": system_message + "비자정책정보: "+st.session_state.visarule},
                    {"role": "user", "content": st.session_state.subjectcase}
                ],
                stream = False
            )
            st_message( stream1.choices[0].message.content.strip(), avatar_style="no-avatar")
            
            
            #가능한 경우 visarule 바탕으로 서류 설명
            if qualifypoint :
                stream2 = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": language_message},
                        {"role": "system", "content": visarule_data},
                        {"role": "user", "content": st.session_state.subjectcase}
                    ],
                    stream = False
                )
                st_message( stream2.choices[0].message.content.strip(), avatar_style="no-avatar")
                    
            #불가능한 경우 assistant_data에 제공되는 상담 사례 설명       
            if not(qualifypoint):
                stream3 = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": language_message},
                    {"role": "system", "content": "Please describe the consultation case specifically. Please include the title or content of the consultation, the result, the law, and the evaluation. Please be specific about the situation and how it was resolved."},
                    {"role": "system", "content": assistant_data},
                    {"role": "user", "content": st.session_state.subjectcase}
                ],
                stream = False
                )
                st_message( stream3.choices[0].message.content.strip(), avatar_style="no-avatar")

            return

            

    
    #############################본문###############################################
    
        def main():
            if st.session_state.flag == "1":
                user_info()
            if st.session_state.flag == "2":
                get_purpose()
            if st.session_state.flag == "3":
                get_answer()
                st.session_state.flag = "7"
            if st.session_state.flag == "4":
                if 'init4' not in st.session_state:
                    bot_avatar_html = f'''
                    <div style="text-align: left;">
                        <img src="https://img.icons8.com/emoji/48/partying-face.png" width="50"/>
                    </div>
                    '''
                    st.markdown(bot_avatar_html, unsafe_allow_html=True)
                    st_message(translate("당신은 제외대상에 해당하지 않습니다. 비자 점수를 측정하고 싶으시면 아래 버튼을 눌러주세요"), avatar_style="no-avatar")
                    st.session_state.init4 = 1
                see_score = st.button(st.session_state.button[2], type="primary")
                if see_score:
                    st.session_state.flag = "6"  # To indicate we are now entering score calculation
                    st.rerun()
            if st.session_state.flag == "5":
                if 'init5' not in st.session_state:
                    bot_avatar_html = f'''
                    <div style="text-align: left;">
                        <img src="https://img.icons8.com/emoji/48/new-moon-face.png" width="50"/>
                    </div>
                    '''
                    st.markdown(bot_avatar_html, unsafe_allow_html=True)
                    st_message(translate("당신은 제외대상에 해당합니다. 상담결과를 보시려면 아래 버튼을 눌러주세요"), avatar_style="no-avatar")
                    st.session_state.init5 = 1
                see_result = st.button(st.session_state.button[0], type="primary")
                if see_result:
                    get_answer()
                    st.session_state.flag = "7"
            if st.session_state.flag == "6":
                get_score()
            if st.session_state.flag == "7":
                chat_again = st.button(st.session_state.button[1], type="primary")
                if chat_again:
                    st.session_state.messages = [{"role": "assistant", "content": "Tell me anything"}]
                    st.session_state.flag = "2"
                    st.rerun()


        if __name__ == "__main__":
            main()
