import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
import base64
import logging
from logging.handlers import TimedRotatingFileHandler
from uuid import uuid4

def initialize_environment_and_path():
    """
    .env 読み込みと PATH(bin) 追加をセッション内で一度だけ実施
    """
    # .env は毎回呼んでも問題ないため先に実行
    load_dotenv()

    if "is_path_ready" not in st.session_state:
        st.session_state.is_path_ready = False

    if not st.session_state.is_path_ready:
        repo_root = Path(__file__).resolve().parent
        bin_dir = repo_root / "bin"
        if bin_dir.exists():
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
        st.session_state.is_path_ready = True

def setup_page_with_wallpaper_and_title():
    """
    ページ設定、壁紙適用、タイトル画像表示
    """
    # 遅延インポートで .env 反映後に constants を読み込む
    from constants import Constants as ct

    st.set_page_config(page_title=ct.APP_NAME)

    # 背景画像CSS
    with open(ct.WALLPAPER_PATH, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-repeat: repeat;
        background-position: center;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    # タイトル
    st.image(ct.TITLE_IMAGE_PATH, width=600)

def initialize_session_state():
    """
    Streamlit セッション状態、OpenAI クライアント、LLM、メモリの初期化
    """
    # 遅延インポート
    from constants import Constants as ct
    from openai import OpenAI
    from langchain_openai import ChatOpenAI
    from langchain.memory import ConversationSummaryBufferMemory

    if "messages" in st.session_state:
        return

    st.session_state.messages = []
    st.session_state.start_flg = False
    st.session_state.pre_mode = ""
    st.session_state.conversation_first_flg = True
    st.session_state.shadowing_flg = False
    st.session_state.shadowing_button_flg = False
    st.session_state.shadowing_count = 0
    st.session_state.shadowing_first_flg = True
    st.session_state.shadowing_audio_input_flg = False
    st.session_state.dictation_flg = False
    st.session_state.dictation_button_flg = False
    st.session_state.dictation_count = 0
    st.session_state.dictation_first_flg = True
    st.session_state.chat_message = ""
    st.session_state.dictation_evaluation_first_flg = True
    st.session_state.chat_open_flg = False
    st.session_state.problem = ""
    st.session_state.save_user_data_flg = False

    st.session_state.openai_obj = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # 日常英会話
    st.session_state.conversation_llm = ChatOpenAI(model_name=ct.CHAT_MODEL_NAME, temperature=ct.CHAT_TEMPERATURE)
    st.session_state.conversation_memory = ConversationSummaryBufferMemory(
        llm=st.session_state.conversation_llm,
        max_token_limit=ct.MEMORY_MAX_TOKEN_LIMIT,
        return_messages=True
    )
    # シャドーイング
    st.session_state.shadowing_llm = ChatOpenAI(model_name=ct.CHAT_MODEL_NAME, temperature=ct.CHAT_TEMPERATURE)
    st.session_state.shadowing_memory = ConversationSummaryBufferMemory(
        llm=st.session_state.shadowing_llm,
        max_token_limit=ct.MEMORY_MAX_TOKEN_LIMIT,
        return_messages=True
    )
    # ディクテーション
    st.session_state.dictation_llm = ChatOpenAI(model_name=ct.CHAT_MODEL_NAME, temperature=ct.CHAT_TEMPERATURE)
    st.session_state.dictation_memory = ConversationSummaryBufferMemory(
        llm=st.session_state.dictation_llm,
        max_token_limit=ct.MEMORY_MAX_TOKEN_LIMIT,
        return_messages=True
    )

def initialize_logger():
    """
    ログ出力の設定（元 functions.initialize_logger）
    """
    # 遅延インポート
    from constants import Constants as ct

    # セッションID
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid4().hex

    os.makedirs(ct.LOG_DIR_PATH, exist_ok=True)
    logger = logging.getLogger(ct.LOGGER_NAME)

    if logger.hasHandlers():
        return

    log_handler = TimedRotatingFileHandler(
        os.path.join(ct.LOG_DIR_PATH, ct.LOG_FILE),
        when=ct.LOG_ROTATION_WHEN,
        encoding=ct.LOG_FILE_ENCODING
    )
    formatter = logging.Formatter(
        ct.LOG_FORMAT_TEMPLATE.replace("%(session_id)s", str(st.session_state.session_id))
    )
    log_handler.setFormatter(formatter)
    logger.setLevel(ct.LOG_LEVEL)
    logger.addHandler(log_handler)
