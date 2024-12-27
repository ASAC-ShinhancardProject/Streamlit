import streamlit as st
import anthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langsmith import Client
from streamlit_feedback import streamlit_feedback
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from pathlib import Path
import pandas as pd
from pptx import Presentation
import io
import time  # 추가된 부분
import docx
import base64
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# API 키 설정
openai_api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

# OpenAI 설정
client = OpenAI(api_key=openai_api_key)

# Streamlit 앱 설정
     # layout="wide" : 페이지가 화면 전체를 사용하도록 지정
st.set_page_config(page_title="집코기", page_icon="🏡", layout="wide")


# <head>
# Google Fonts에서 원하는 폰트 로드
    # 현재는 Black Han Sans, Do Hyeon, Jua 세 가지 폰트를 로드하고 있음 (한국어에 적합한 폰트임)

# <style>
    # .custom-title라는 클래스를 생성하여 텍스트 스타일을 설정
        # !important
            # 이 속성을 다른 CSS 규칙보다 우선 적용하도록 설정
        # font-family: 'Jua', sans-serif
            # Jua 폰트를 기본으로 사용하고, Jua 폰트가 없는 환경에서는 sans-serif 폰트를 사용
        # font-size: 30px
            #  텍스트 크기를 30픽셀로 설정
	    # font-weight: 700
            # 텍스트의 굵기를 700(굵은 글씨)로 설정 (숫자가 높을수록 글씨가 더 굵게 표시)

st.markdown("""
<head>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&display=swap">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Do+Hyeon&display=swap">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jua&display=swap">
<style>
.custom-title {
    font-family: 'Jua', sans-serif !important;
    font-size: 30px !important;
    font-weight: 700 !important;
}
.custom-title1 {
    font-family: 'Do Hyeon', sans-serif !important; 
    font-size: 15px !important;
    font-weight: 10% !important;
}

</style>
</head>
""", unsafe_allow_html=True)    # 기본적으로 Streamlit은 보안상 HTML을 허용하지 않지만, unsafe_allow_html=True 를 사용하면 HTML 태그를 사용할 수 있음


# 현재 스크립트의 디렉토리를 기준으로 assets 폴더 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, 'static')

# static 폴더에 bot_character.png와 human_character.png라는 파일을 저장했다면 해당 이미지가 각각 챗봇과 사용자의 아바타 이미지로 사용됨
    # '채팅 기록에서 가장 최근 메시지만 표시' 주석을 살펴보면 avatar="챗봇.png"로 명시되어 있기 때문에 지정된 "챗봇.png" 파일을 그대로 사용한다
    # 즉, 현재 코드에서는 get_avatar_path를 사용하지 않는다
        # 맨 아래에 주석으로 코드를 달아놓겠음

def get_avatar_path(role: str) -> str:
    """이미지 파일의 절대 경로를 반환"""
    image_path = os.path.join(ASSETS_DIR, f'{role}_character.png')
    if os.path.exists(image_path):
        return image_path
    print(f"Warning: Image not found at {image_path}")  # 디버깅용
    return None

def send_message(message, role, save=True):
    """Display message with appropriate avatar"""
    avatar_path = get_avatar_path('human' if role == 'human' else 'bot')
    try:
        with st.chat_message(role, avatar=avatar_path):             # st.chat_message를 사용해 Streamlit의 대화형 메시지 구성 요소로 메시지를 출력
            st.markdown(message, unsafe_allow_html=True)
        if save:  # 메시지를 한 번만 저장
            save_message(message, role)
    except Exception as e:
        print(f"Error displaying message with avatar: {e}")
        with st.chat_message(role):
            st.markdown(message, unsafe_allow_html=True)
        if save:
            save_message(message, role)

def get_image_as_base64(image_path):
    """이미지를 Base64 문자열로 변환"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception as e:
        st.error(f"이미지를 불러오는 중 오류가 발생했습니다: {e}")
        return ""
    

# 배경 이미지 추가
bg_image_path = "static/bg.png"  # 배경 이미지 경로

# <style>
# background-size: cover;
    # 이미지를 화면 크기에 맞게 조정
# background-attachment: fixed;
    # 스크롤을 해도 배경 이미지가 고정되어 움직이지 않음
# background-repeat: no-repeat;
    # 이미지를 반복하지 않음

#  data-testid = 
    # Streamlit 컴포넌트를 선택하는 데 사용
# .stMain:
	# Streamlit 앱의 주요 콘텐츠 영역을 선택

if Path(bg_image_path).exists():
    bg_image_base64 = get_image_as_base64(bg_image_path)
    st.markdown(
        f"""
        <style>
        /* 전체 페이지 배경 */
        html {{
            background-image: url("data:image/png;base64,{bg_image_base64}");
            background-size: cover; 
            background-attachment: fixed;
            background-repeat: no-repeat;
        }}

        /* 텍스트 입력창 하단 영역 (stChatInput) */
        [data-testid="stApp"]{{
            background-image: url("data:image/png;base64,{bg_image_base64}");
            background-size: cover;
    /       background: rgba(255, 255, 255, 0); /* 투명화 *
        }}
        
        /* 사이드바 배경 투명화 */
        [data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0); /* 투명화 */
        }}
        
        /* 사이드바 배경 투명화 */
        [data-testid="stHeader"] {{
            background: rgba(255, 255, 255, 0); /* 투명화 */
        }}
        
        /* 사이드바 배경 투명화 */
        [data-testid="stBottom"] {{
            background: rgba(255, 255, 255, 0); /* 투명화 */
        }}
        
        /* 사이드바 배경 투명화 */
        [data-testid="stBottom"] > div {{
            background: rgba(255, 255, 255, 0); /* 투명화 */
        }}
        
        /*특정 영역 색상 변경 */
        .stMain {{
            background: rgba(255, 255, 255, 255); /* 투명화 */
        }}
        """,
        unsafe_allow_html=True
    )
else:
    st.warning("배경 이미지 파일이 존재하지 않습니다.")



# 페이지 제목
st.markdown('<h1 class="custom-title">🏡 집코기</h1>', unsafe_allow_html=True)
#st.markdown('<h3 class="custom-title1"> 아파트에 관해 물어보세요 (아파트 정보, 청약, 대출, 세금 등) </h3>', unsafe_allow_html=True)


if not openai_api_key:
    st.error("OpenAI API key 설정을 확인해주시기 바랍니다.")
    st.stop()

# 프롬프트
content_chatbot="당신은 친절한 부동산 전문가입니다. 사용자에게 명확하고 간결하게 이해할 수 있는 방식으로 설명하며, \
                전문성을 가지고, 항상 친절한 어조를 유지합니다. bold체를 사용하여 가독성 좋게 대답합니다.\
                정보는 제공된 문서와 로컬환경에서 찾아오며 출처를 정확하게 표시합니다.\
                Mark the source, including the link from the source, at the end of the information you find. \
                If you find the info from the uploaded document, mark it as (학습문서)\
                검색된 컨텍스트의 다음 부분을 사용하여 질문에 답변하세요. \
                답을 모르는 경우 모른다고 말하세요. \
                문서에서 정보를 가져올 경우 문단 구분을 잘 해야합니다.\
                대답이 길어질 경우 줄바꿈을 통해 가독성을 높입니다. 이전의 대화 내용을 잘 기억하여 대화 맥락을 파악합니다."

# 세션 상태 초기화
    # 세션 상태가 처음 설정될 때만 이 코드가 실행된다
    # 이미 초기화된 세션에 대해 다시 초기화하지 않도록 설정
if 'initialized' not in st.session_state:
    st.session_state.file_qa_messages = [SystemMessage(content = content_chatbot)]  # file_qa_messages : 대화 기록을 저장하기 위한 변수 / 리스트 형태로 대화 메세지를 순차적으로 저장
                                                                                    # SystemMessage(content=content_chatbot) : content_chatbot 변수에 저장된 프롬프트를 기반으로 초기 메시지를 설정
    st.session_state.file_qa_content = None     # 업로드된 파일의 텍스트 데이터를 저장하기 위한 변수 / 초기값은 None으로 설정하여 파일이 업로드되지 않았음을 나타냄
    st.session_state.file_qa_data = None        # 업로드된 파일에서 변환된 구조화된 데이터(예: pandas DataFrame)를 저장하는 변수 / PDF, Word, Excel 등의 파일을 업로드한 후 이를 처리한 결과가 여기에 저장됨
    st.session_state.initialized = True         # 세션 상태가 초기화되었음을 나타내는 플래그 / Streamlit은 기본적으로 페이지를 새로고침할 때마다 코드를 다시 실행하지만 해당 옵션을 True로 사옹하면 상태를 유지함
    st.session_state.greeting_displayed = False  # 인사 표시 여부를 추적하는 새로운 변수 / 앱이 처음 실행되었을 때, 챗봇이 사용자에게 인사 메시지를 표시하도록 설정


# 사이드바에 파일 업로드 위젯 추가
with st.sidebar:
    st.markdown("**[만든사람]** 이일섭 연짱 쏴리 도핑 쪼링")    # **만든 사람**을 굵게 표시
    #st.markdown("File Upload (Optional)")
    uploaded_file = st.file_uploader("Upload a file", type=("docx", "pdf", "csv", "xlsx", "pptx"))  # Streamlit에서 제공하는 파일 업로드 위젯
    if uploaded_file:
        st.success(f"File '{uploaded_file.name}' uploaded successfully.")

# 채팅 초기화 버튼
reset_history = st.sidebar.button("채팅 초기화")

if reset_history:
    st.session_state.file_qa_messages = []      # 대화 기록을 저장하는 세션 변수를 빈 리스트로 초기화하여 기존 대화 기록을 삭제함
    st.session_state.file_qa_content = None     # 업로드된 파일의 텍스트 데이터를 저장하는 변수를 None으로 초기화하여 업로드된 파일 내용을 삭제함
    st.session_state.greeting_displayed = False  # 초기화 시 인사 표시 상태도 초기화 / 밑에서 인사 메시지 생성 후 True로 바뀜
### 업로드된 파일 크기 제한을 추가하거나 파일이 너무 클 경우 에러 메시지 표시를 하는 건 어떨까???


# 파일 처리 함수
def process_file(file):
    if file is None:
        return None, None
    try:
        # 텍스트 파일 내용을 UTF-8 디코딩하여 텍스트 문자열로 변환
        if file.type == "text/plain":
            content = file.read().decode()
            return content, None
        
        # PyPDF2의 PdfReader를 사용하여 PDF 파일에서 텍스트를 추출 / 각 페이지의 텍스트를 읽어 하나의 문자열로 병합
        elif file.type == "application/pdf":
            pdf_reader = PdfReader(io.BytesIO(file.read()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text, None
        
        # pandas의 read_csv를 사용하여 CSV 데이터를 DataFrame으로 로드 / 텍스트로 보기 위해 DataFrame을 문자열로 변환(df.to_string()) / 데이터와 텍스트 내용을 모두 반환
        elif file.type == "text/csv":
            df = pd.read_csv(file)
            return df.to_string(), df
        
        # CSV와 동일하게 텍스트와 데이터 둘 다 반환 / pandas의 read_excel 사용
            # sheet는 반드시 하나여만 하는 듯?
        elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            df = pd.read_excel(file)
            return df.to_string(), df
        
        # python-pptx의 Presentation 객체를 사용하여 슬라이드 텍스트 추출 / 각 슬라이드의 텍스트를 하나의 문자열로 병합
        elif file.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            prs = Presentation(file)
            text = ""
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, 'text'):
                        text += shape.text + "\n"
            return text, None
        
        # python-docx를 사용하여 Word 파일 내용을 추출 / 각 문단의 텍스트를 하나의 문자열로 병합
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":  # 추가된 부분
            doc = docx.Document(file)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text, None
        
        # 지원하지 않는 파일 형식의 경우 오류 메세지와 None 반환
        else:
            return f"Unsupported file type: {file.type}", None
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None, None
    

# 파일 업로드 및 처리
if uploaded_file:
    with st.spinner("Processing uploaded file..."):
        st.session_state.file_qa_content, st.session_state.file_qa_data = process_file(uploaded_file)
        if st.session_state.file_qa_content:
            st.sidebar.success(f"File '{uploaded_file.name}' processed successfully.")
        else:
            st.sidebar.error("Failed to process the file.")

# 챗봇 응답 함수
def get_chatbot_response(prompt, file_content=None):
    try:
        messages = [
            {"role": "system", "content": content_chatbot},     # content_chatbot 프롬프트를 사용해 챗봇의 역할과 응답 스타일을 정의
            {"role": "user", "content": prompt}     # prompt : 사용자가 입력한 질문 또는 요청
        ]

        response = client.chat.completions.create(      # client.chat.completions.create : OpenAI GPT 모델을 호출하는 함수
            model="gpt-4o-mini",        # 사용할 모델 이름
            messages=messages,
            max_tokens=3200,            # 모델이 생성할 최대 토큰 수 / GPT-4o-mini의 최대 토큰 수는 4096일 가능성 (확인 필요)
        )

        response_text = response.choices[0].message.content     # 첫번째 응답(choices[0])에서 텍스트 내용(message.content)을 추출하여 반환
        return response_text
    except Exception as e:
        st.error(f"Error in chatbot response: {str(e)}")
        return None

# 스트리밍 응답 함수
    # 사용자가 텍스트가 생성되는 것처럼 느낄 수 있는 시각적 효과를 제공
def stream_response(response_text, response_container):
    response = ""       # 표시될 응답 텍스트를 저장할 변수를 초기화
    for char in response_text:
        response += char    # 현재 문자를 기존 응답 텍스트에 추가 / 한 글자 씩
        response_container.markdown(response, unsafe_allow_html=True)
        time.sleep(0.01)    # 각 문자를 표시하기 전에 약간의 지연(0.01초)을 추가



# 사이드바에서 텍스트 분석 챗봇 모드 추가
def create_sidebar_with_text_analysis():
    """사이드바에서 텍스트 분석 챗봇 모드를 추가합니다."""
    with st.sidebar:
        st.markdown("### 🤖 챗봇 모드 선택")
        
        # 모드 선택
        mode = st.radio(
            "원하시는 모드를 선택하세요:",
            ["부동산 인사이트", "부동산 정책/금융"],        # 기본적으로 '부동산 인사이트'가 선택된다 / 현재 해당 기능을 화면에서 찾을 수 없다 (확인 필요)
            index=0,
            key="chat_mode_sidebar"  # 고유 키로 변경
        )
        
        # 세션 상태 업데이트
        st.session_state.analysis_mode = (mode == "텍스트 분석 챗봇")

# 인사 메시지 표시 (챗봇이 먼저 인사)
if not st.session_state.greeting_displayed:
    initial_message = AIMessage(content="안녕하세요. 아파트 시장에 대해 물어보세요 😊  \n"
                                        "내 집 마련과 시장 정보에 대한 질문 및 답변이 가능합니다")
    st.session_state.file_qa_messages.append(initial_message)       # file_qa_messages 리스트는 대화 메시지를 저장하는 세션 상태 변수 / 생성한 초기 메시지를 리스트에 추가하여 저장
    st.session_state.greeting_displayed = True  # 인사를 표시했음을 기록


# 채팅 기록에서 가장 최근 메시지만 표시
if st.session_state.file_qa_messages:   # 리스트가 비어 있지 않다면 가장 최근 메시지를 가져옴
    last_message = st.session_state.file_qa_messages[-1]    # 리스트의 마지막 메시지를 가져옴
    if isinstance(last_message, AIMessage):     # 가져온 메시지가 챗봇 메시지인지, 사용자 메시지인지 확인
        st.chat_message("ai", avatar="챗봇.png").write(last_message.content)
    elif isinstance(last_message, HumanMessage):
        st.chat_message("human", avatar="질문.png").write(last_message.content)


# 사용자 입력 처리
if prompt := st.chat_input("부동산 시장에 관해 물어보세요"):        # 사용자로부터 입력을 받는 Streamlit의 입력 위젯 / 괄호 안에는 안내문
    # 사용자 질문 메시지 출력 및 저장
    with st.chat_message("human", avatar="질문.png"):         # 사용자의 메시지를 화면에 표시 / 사용자의 아바타 이미지 설정
        formatted_prompt = prompt.replace("\n", "<br>")      # 입력된 메시지에서 줄바꿈(\n)을 HTML의 <br> 태그로 대체하여 웹 화면에서 올바르게 줄바꿈이 표시되도록 처리
        st.markdown(f'<div class="user-message">{formatted_prompt}</div>', unsafe_allow_html=True)  # st.markdown을 사용해 포맷된 사용자 메시지를 HTML 형식으로 표시
    st.session_state.file_qa_messages.append(HumanMessage(content=prompt))      # HumanMessage(content=prompt)를 생성하여 사용자의 메시지를 대화 기록(file_qa_messages)에 추가

    # 새로운 질문에 대한 응답 생성
    with st.chat_message("ai", avatar="챗봇.png"):
        response_container = st.empty()  # 여기서 새로운 빈 컨테이너 생성
        with st.spinner("답변생성중..."):       # 챗봇 응답 생성 중임을 사용자에게 표시하는 스피너 UI
            response = get_chatbot_response(prompt, st.session_state.file_qa_content)       # prompt(사용자 입력)와 st.session_state.file_qa_content(업로드된 파일의 텍스트 데이터)을 입력으로 받아 챗봇 응답을 생성

            if response:
                st.session_state.file_qa_messages.append(AIMessage(content=response))       # 챗봇의 응답 메시지를 AIMessage 객체로 생성하여 대화 기록(file_qa_messages)에 추가
                stream_response(response, response_container)  # 여기서 response_container를 인자로 전달 / 챗봇 응답을 글자 단위로 스트리밍 방식으로 출력
            else:
                response_container.error("Failed to get a response. Please try again.")     # 응답에 실패한 경우 에러 메시지 출력



# 피드백 수집
if len(st.session_state.file_qa_messages) > 1:
    last_message = st.session_state.file_qa_messages[-1]
    if isinstance(last_message, AIMessage):
        feedback = streamlit_feedback(
            feedback_type="thumbs",
            key=f"file_qa_feedback_{len(st.session_state.file_qa_messages)}"
        )
        if feedback:
            score = 1 if feedback["score"] == "thumbsup" else 0
            client = Client()
            run_id = client.create_run(
                project_name=os.getenv("LANGCHAIN_PROJECT"),
                name="File Q&A Interaction",
                inputs={"messages": [msg.content for msg in st.session_state.file_qa_messages[1:]]},
            ).id
            client.create_feedback(run_id, "user_score", score=score)
            st.toast("Feedback submitted!", icon="✅")





# get_avatar_path를 사용하려면 아래 코드 참고

# if st.session_state.file_qa_messages:
#     last_message = st.session_state.file_qa_messages[-1]
#     if isinstance(last_message, AIMessage):
#         avatar_path = get_avatar_path('bot')  # bot_character.png 경로 가져오기
#         st.chat_message("ai", avatar=avatar_path).write(last_message.content)
#     elif isinstance(last_message, HumanMessage):
#         avatar_path = get_avatar_path('human')  # human_character.png 경로 가져오기
#         st.chat_message("human", avatar=avatar_path).write(last_message.content)



# # 사용자 입력 처리
# if prompt := st.chat_input("부동산 시장에 관해 물어보세요"):
#     # 사용자 질문 메시지 출력 및 저장
#     with st.chat_message("human", avatar=get_avatar_path("human")):
#         formatted_prompt = prompt.replace("\n", "<br>")
#         st.markdown(f'<div class="user-message">{formatted_prompt}</div>', unsafe_allow_html=True)
#     st.session_state.file_qa_messages.append(HumanMessage(content=prompt))

#     # 새로운 질문에 대한 응답 생성
#     with st.chat_message("ai", avatar=get_avatar_path("bot")):
#         response_container = st.empty()
#         with st.spinner("답변생성중..."):
#             response = get_chatbot_response(prompt, st.session_state.file_qa_content)

#             if response:
#                 st.session_state.file_qa_messages.append(AIMessage(content=response))
#                 stream_response(response, response_container)
#             else:
#                 response_container.error("Failed to get a response. Please try again.")