import streamlit as st
import audio_util as au
import functions as ft
from constants import Constants as ct
from datetime import datetime
import re

def _ensure_problem_chain():
    """
    初回のみ、ディクテーション用の問題生成Chainを作成
    """
    now = datetime.now()
    current_datetime = now.strftime("%Y-%m-%d %H:00")

    if st.session_state.dictation_first_flg:
        st.session_state.chain_create_problem = ft.create_chain(
            ct.SYSTEM_TEMPLATE_CREATE_PROBLEM.format(CURRENT_DATETIME=current_datetime, CHAR_COUNT=ct.PROBLEM_CHAR_COUNT[st.session_state.englv]),
            st.session_state.dictation_llm,
            st.session_state.dictation_memory
        )
        st.session_state.dictation_first_flg = False

def _generate_and_read_problem():
    """
    問題文を生成して読み上げ、次ターンで評価を行うためのフラグを更新
    """
    with st.spinner(ct.SPINNER_CREATE_PROBLEM):
        st.session_state.problem, _ = au.create_problem_and_play_audio()
    # 次はチャット入力を受け付けて評価へ
    st.session_state.chat_open_flg = True
    st.session_state.dictation_flg = False
    st.rerun()

def _show_messages_for_evaluation():
    """
    評価表示前に、AIの問題文とユーザーの回答をチャットに表示し、履歴へ追加
    """
    with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
        st.markdown(st.session_state.problem)
    with st.chat_message("user", avatar=ct.USER_ICON_PATH):
        st.markdown(st.session_state.chat_message)

    st.session_state.messages.append({"role": "assistant", "content": st.session_state.problem})
    st.session_state.messages.append({"role": "user", "content": st.session_state.chat_message})

def _create_and_run_evaluation() -> str:
    """
    評価用Chainを作成し、評価結果テキストを生成して返す
    """
    print("\n\nuser_text:", st.session_state.chat_message)
    if not re.search(r"[A-Za-z]", st.session_state.chat_message):
        return ct.EVALUATION_NO_INPUT_MESSAGE
    
    system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
        llm_text=st.session_state.problem,
        user_text=st.session_state.chat_message
    )
    st.session_state.chain_evaluation = ft.create_chain(
        system_template,
        st.session_state.dictation_llm,
        st.session_state.dictation_memory
    )
    llm_response_evaluation = st.session_state.chain_evaluation.predict(input="")
    return llm_response_evaluation

def _update_flags_after_evaluation():
    """
    評価後の各種フラグを更新（次ターンの準備）
    """
    st.session_state.dictation_flg = True
    st.session_state.chat_message = ""
    st.session_state.dictation_count += 1
    st.session_state.chat_open_flg = False
    st.rerun()

def run_dictation_mode():
    """
    ディクテーションモードのメイン処理を実行
    - 初回の問題生成用Chain作成
    - 問題文の生成と読み上げ
    - チャット入力時の評価処理
    """
    # Chainの用意
    _ensure_problem_chain()

    # チャット入力以外（問題の生成と読み上げ）
    if not st.session_state.chat_open_flg:
        _generate_and_read_problem()
        return

    # チャット入力がない場合は評価せずに停止
    if not st.session_state.chat_message:
        st.stop()
        return

    # 評価表示前のメッセージ描画と履歴追加
    _show_messages_for_evaluation()

    # 評価の実行
    with st.spinner(ct.SPINNER_EVALUATION):
        llm_response_evaluation = _create_and_run_evaluation()

    # 評価結果の表示と履歴追加
    with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
        st.markdown(llm_response_evaluation)
    st.session_state.messages.append({"role": "assistant", "content": llm_response_evaluation})
    st.session_state.messages.append({"role": "other"})

    # フラグ更新と次ターンへ
    _update_flags_after_evaluation()
