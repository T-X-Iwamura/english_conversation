import streamlit as st
import audio_util as au
import functions as ft
from constants import Constants as ct
import time 
from datetime import datetime
import re

def _ensure_problem_chain():
    """
    初回のみ、シャドーイング用の問題生成Chainを作成
    """
    now = datetime.now()
    current_datetime = now.strftime("%Y-%m-%d %H:00")
    
    if st.session_state.shadowing_first_flg:
        st.session_state.chain_create_problem = ft.create_chain(
            ct.SYSTEM_TEMPLATE_CREATE_PROBLEM.format(CURRENT_DATETIME=current_datetime, CHAR_COUNT=ct.PROBLEM_CHAR_COUNT[st.session_state.englv]),
            st.session_state.shadowing_llm,
            st.session_state.shadowing_memory
        )
        st.session_state.shadowing_first_flg = False

def _maybe_generate_and_read_problem():
    """
    問題文の生成と読み上げ（必要な場合のみ実行）
    """
    if not st.session_state.shadowing_audio_input_flg:
        with st.spinner(ct.SPINNER_CREATE_PROBLEM):
            st.session_state.problem, _ = au.create_problem_and_play_audio()

def _record_and_transcribe() -> str:
    """
    録音し、文字起こしテキストを返す
    """
    st.session_state.shadowing_audio_input_flg = True
    audio_input_file_path = f"{ct.AUDIO_INPUT_DIR}/{ct.AUDIO_INPUT_FILENAME_PREFIX}{int(time.time())}.wav"
    au.record_audio(audio_input_file_path)
    st.session_state.shadowing_audio_input_flg = False

    with st.spinner(ct.SPINNER_TRANSCRIBE):
        transcript = au.transcribe_audio(audio_input_file_path)
        return transcript.text

def _show_exchange(problem_text: str, user_text: str):
    """
    画面にAIの問題文とユーザーの発話を表示し、履歴に追加
    """
    with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
        st.markdown(problem_text)
    with st.chat_message("user", avatar=ct.USER_ICON_PATH):
        st.markdown(user_text)

    st.session_state.messages.append({"role": "assistant", "content": problem_text})
    st.session_state.messages.append({"role": "user", "content": user_text})

def _evaluate_if_needed(problem_text: str, user_text: str) -> str:
    """
    評価用のChainを用意（初回のみ）し、評価結果を返す
    """
    if not re.search(r"[A-Za-z]", user_text):
        return ct.EVALUATION_NO_INPUT_MESSAGE
    
    system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
        llm_text=problem_text,
        user_text=user_text
    )
    st.session_state.chain_evaluation = ft.create_chain(
        system_template,
        st.session_state.shadowing_llm,
        st.session_state.shadowing_memory
    )

    # 問題文と回答を比較し、評価結果の生成
    return ft.create_evaluation()

def _append_evaluation_and_flags(llm_response_evaluation: str):
    """
    評価結果の表示・履歴追加、および各種フラグ更新
    """
    with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
        st.markdown(llm_response_evaluation)
    st.session_state.messages.append({"role": "assistant", "content": llm_response_evaluation})
    st.session_state.messages.append({"role": "other"})

    # 各種フラグの更新
    st.session_state.shadowing_flg = True
    st.session_state.shadowing_count += 1

    # 次のターンのために再描画
    st.rerun()

def run_shadowing_mode():
    """
    シャドーイングモードのメイン処理
    - 初回の問題生成用Chain作成
    - 必要に応じた問題生成・読み上げ
    - 録音→文字起こし→評価→表示→フラグ更新
    """
    # 初回の問題生成チェーン準備
    _ensure_problem_chain()

    # 必要に応じて問題生成と読み上げ
    _maybe_generate_and_read_problem()

    # 録音と文字起こし
    audio_input_text = _record_and_transcribe()

    # 表示と履歴追加
    _show_exchange(st.session_state.problem, audio_input_text)

    # 評価
    with st.spinner(ct.SPINNER_EVALUATION):
        llm_response_evaluation = _evaluate_if_needed(st.session_state.problem, audio_input_text)

    # 評価の表示とフラグ更新
    _append_evaluation_and_flags(llm_response_evaluation)
