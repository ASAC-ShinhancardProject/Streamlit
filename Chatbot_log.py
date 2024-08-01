from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables import RunnableConfig
from langchain_core.tracers import LangChainTracer
from langchain_core.tracers.run_collector import RunCollectorCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langsmith import Client
from langsmith.utils import LangSmithNotFoundError, LangSmithConnectionError
import streamlit as st
from streamlit_feedback import streamlit_feedback
import time
import os
import requests
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

st.set_page_config(page_title="ChatBot with LangSmith", page_icon="🤖")
st.title("🤖OPENAI API 챗봇")

# 현재 페이지 이름 가져오기 (수정된 부분)
current_page = st.query_params.get("page", "main")


# LangSmith 환경 변수 설정
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN_ENDPOINT"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN_PROJECT"]
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]

# LangSmith 설정 확인
langsmith_settings = {
    "LANGCHAIN_API_KEY": os.getenv("LANGCHAIN_API_KEY"),
    "LANGCHAIN_PROJECT": os.getenv("LANGCHAIN_PROJECT"),
    "LANGCHAIN_ENDPOINT": os.getenv("LANGCHAIN_ENDPOINT"),
    "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2")
}

st.sidebar.subheader("LangSmith 설정")
for key, value in langsmith_settings.items():
    if key == "LANGCHAIN_API_KEY" and value:
        st.sidebar.text(f"{key}: {'*' * len(value)}")  # API 키 마스킹
    else:
        st.sidebar.text(f"{key}: {value}")

# LangSmith 클라이언트 및 트레이서 설정
try:
    client = Client()
    st.sidebar.success("LangSmith 클라이언트가 성공적으로 초기화되었습니다.")
    ls_tracer = LangChainTracer(project_name=os.environ["LANGCHAIN_PROJECT"], client=client)
    run_collector = RunCollectorCallbackHandler()
    cfg = RunnableConfig()
    cfg["callbacks"] = [ls_tracer, run_collector]
    cfg["configurable"] = {"session_id": "any"}
except Exception as e:
    st.sidebar.error(f"LangSmith 클라이언트 초기화 중 오류 발생: {str(e)}")

# LangSmith 연결 테스트
def test_langsmith_connection():
    try:
        response = requests.get(os.getenv("LANGCHAIN_ENDPOINT"), timeout=5)
        if response.status_code == 200:
            return "LangSmith 서버에 연결할 수 있습니다."
        else:
            return f"LangSmith 서버 응답 오류: 상태 코드 {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"LangSmith 서버 연결 실패: {str(e)}"

st.sidebar.text(test_langsmith_connection())

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

# 채팅 기록 설정
if f"messages_{current_page}" not in st.session_state:
    st.session_state[f"messages_{current_page}"] = []

msgs = StreamlitChatMessageHistory(key=f"langchain_messages_{current_page}")

# 기존 메시지 변환
converted_messages = []
for msg in st.session_state[f"messages_{current_page}"]:
    if isinstance(msg, dict):
        if msg['role'] == 'assistant':
            converted_messages.append(AIMessage(content=msg['content']))
        elif msg['role'] == 'user':
            converted_messages.append(HumanMessage(content=msg['content']))
    else:
        converted_messages.append(msg)
st.session_state[f"messages_{current_page}"] = converted_messages


# 채팅 초기화 버튼
reset_history = st.sidebar.button("채팅 초기화")

if reset_history:
    st.session_state[f"messages_{current_page}"] = []
    msgs.clear()
    st.session_state[f"last_run_{current_page}"] = None

# 채팅이 비어있으면 초기 메시지 추가
if len(st.session_state[f"messages_{current_page}"]) == 0:
    initial_message = AIMessage(content="무엇을 도와드릴까요?")
    st.session_state[f"messages_{current_page}"].append(initial_message)
    msgs.add_ai_message("무엇을 도와드릴까요?")

# 채팅 기록 표시
for msg in st.session_state[f"messages_{current_page}"]:
    if isinstance(msg, AIMessage):
        st.chat_message("ai").write(msg.content)
    elif isinstance(msg, HumanMessage):
        st.chat_message("human").write(msg.content)
    elif isinstance(msg, dict):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        st.chat_message(role).write(content)
    else:
        st.warning(f"Unexpected message type: {type(msg)}")


# 프롬프트 템플릿 설정
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "한글로 간결하게 답변하세요."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

# 사용자 입력 처리
if user_input := st.chat_input():
    # 사용자 메시지를 즉시 표시 및 저장
    st.chat_message("human").write(user_input)
    user_message = HumanMessage(content=user_input)
    st.session_state[f"messages_{current_page}"].append(user_message)
    msgs.add_user_message(user_input)

    # AI 응답 생성을 위한 플레이스홀더 생성
    ai_response_placeholder = st.empty()

    with ai_response_placeholder.container():
        with st.chat_message("ai"):
            with st.spinner("AI가 응답을 생성 중입니다..."):
                stream_handler = StreamHandler(st.empty())
                llm = ChatOpenAI(streaming=True, callbacks=[stream_handler])
                chain = prompt | llm
                chain_with_history = RunnableWithMessageHistory(
                    chain,
                    lambda session_id: msgs,
                    input_messages_key="question",
                    history_messages_key="history",
                )
                response = chain_with_history.invoke({"question": user_input}, cfg)
                
                # AI 메시지를 저장
                ai_message = AIMessage(content=response.content)
                st.session_state.messages.append(ai_message)
                msgs.add_ai_message(response.content)
    
    st.session_state[f"last_run_{current_page}"] = run_collector.traced_runs[0].id
    st.rerun()

# LangSmith 실행 URL 가져오기
@st.cache_data(ttl="2h", show_spinner=False)
def get_run_url(run_id):
    try:
        time.sleep(1)
        run = client.read_run(run_id)
        return run.url
    except LangSmithNotFoundError:
        st.warning(f"LangSmith 실행 정보를 찾을 수 없습니다. 실행 ID: {run_id}")
        return None
    except LangSmithConnectionError as e:
        st.error(f"LangSmith 서버 연결 오류: {str(e)}")
        return None
    except Exception as e:
        st.error(f"LangSmith 정보 조회 중 예상치 못한 오류 발생: {str(e)}")
        return None

# 피드백 및 LangSmith 링크 표시
if st.session_state.get(f"last_run_{current_page}"):
    run_url = get_run_url(st.session_state[f"last_run_{current_page}"])
    if run_url:
        st.sidebar.markdown(f"[LangSmith 추적🛠️]({run_url})")
    
    feedback = streamlit_feedback(
        feedback_type="thumbs",
        optional_text_label=None,
        key=f"feedback_{st.session_state[f'last_run_{current_page}']}",
    )
    if feedback:
        scores = {"👍": 1, "👎": 0}
        try:
            client.create_feedback(
                st.session_state[f"last_run_{current_page}"],
                feedback["type"],
                score=scores[feedback["score"]],
                comment=feedback.get("text", None),
            )
            st.toast("피드백을 저장하였습니다!", icon="📝")
        except Exception as e:
            st.error(f"피드백 저장 중 오류가 발생했습니다: {str(e)}")

# 사이드바에 추가 정보
with st.sidebar:
    "[신한카드](https://www.shinhancard.com)"
    "[View the source code](https://github.com/jungh5/chat_start/blob/main/Chatbot_log.py)"
    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"