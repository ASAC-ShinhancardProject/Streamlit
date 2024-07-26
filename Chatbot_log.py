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
import streamlit as st
from streamlit_feedback import streamlit_feedback
import time
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

st.set_page_config(page_title="ChatBot with LangSmith", page_icon="🤖")
st.title("🤖OPENAI API 챗봇")

# LangSmith 환경 변수 설정
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN_ENDPOINT"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN_PROJECT"]
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]

# LangSmith 클라이언트 및 트레이서 설정
client = Client()
ls_tracer = LangChainTracer(project_name=os.environ["LANGCHAIN_PROJECT"], client=client)
run_collector = RunCollectorCallbackHandler()
cfg = RunnableConfig()
cfg["callbacks"] = [ls_tracer, run_collector]
cfg["configurable"] = {"session_id": "any"}

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

# 채팅 기록 설정
if "messages" not in st.session_state:
    st.session_state.messages = []

msgs = StreamlitChatMessageHistory(key="langchain_messages")

# 채팅 초기화 버튼
reset_history = st.sidebar.button("채팅 초기화")

if reset_history:
    st.session_state.messages = []
    msgs.clear()
    st.session_state["last_run"] = None

# 채팅이 비어있으면 초기 메시지 추가
if len(st.session_state.messages) == 0:
    initial_message = AIMessage(content="무엇을 도와드릴까요?")
    st.session_state.messages.append(initial_message)
    msgs.add_ai_message("무엇을 도와드릴까요?")

# 채팅 기록 표시
for msg in st.session_state.messages:
    st.chat_message(msg.type).write(msg.content)

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
    st.session_state.messages.append(HumanMessage(content=user_input))
    msgs.add_user_message(user_input)
    st.chat_message("human").write(user_input)
    with st.chat_message("ai"):
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
        st.session_state.messages.append(AIMessage(content=response.content))
        msgs.add_ai_message(response.content)
    st.session_state.last_run = run_collector.traced_runs[0].id

# LangSmith 실행 URL 가져오기
@st.cache_data(ttl="2h", show_spinner=False)
def get_run_url(run_id):
    time.sleep(1)
    return client.read_run(run_id).url

# 피드백 및 LangSmith 링크 표시
if st.session_state.get("last_run"):
    run_url = get_run_url(st.session_state.last_run)
    st.sidebar.markdown(f"[LangSmith 추적🛠️]({run_url})")
    feedback = streamlit_feedback(
        feedback_type="thumbs",
        optional_text_label=None,
        key=f"feedback_{st.session_state.last_run}",
    )
    if feedback:
        scores = {"👍": 1, "👎": 0}
        client.create_feedback(
            st.session_state.last_run,
            feedback["type"],
            score=scores[feedback["score"]],
            comment=feedback.get("text", None),
        )
        st.toast("피드백을 저장하였습니다!", icon="📝")

# 사이드바에 추가 정보
with st.sidebar:
    "[신한카드](https://www.shinhancard.com)"
    "[View the source code](https://github.com/jungh5/chat_start/blob/main/Chatbot_log.py)"
    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"