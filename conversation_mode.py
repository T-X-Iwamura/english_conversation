import streamlit as st
import audio_util as au
import functions as ft
import users_data_storage as ud
from constants import Constants as ct
from user_memory import UserMemory
import json
import time

def _prepare_conversation_chain_if_needed():
    """
    初回のみ、過去のユーザーメモリを読み込み、会話用Chainとメモリを準備
    """
    if not st.session_state.conversation_first_flg:
        return

    user_memory = UserMemory()
    if not st.session_state.user_name == "":
        with st.spinner(ct.LOADING_USER_DATA):
            user_memory = ud.load_user_memory(st.session_state.user_name)
    
    # 過去のプロフィール・長期記憶・サマリーがある場合は冒頭プロンプトを付与
    if user_memory.profile or user_memory.long_memory or user_memory.summary:
        previous_summary = ct.SYSTEM_TEMPLATE_PREVIOUS_CONVERSATION_ORDER.format(
            PROFILE_TEXT=json.dumps(user_memory.profile, ensure_ascii=False),
            LONG_MEMORY_TEXT=json.dumps(user_memory.long_memory, ensure_ascii=False),
            SUMMARY_TEXT=user_memory.summary
        )
        system_template = ct.SYSTEM_TEMPLATE_BASIC_CONVERSATION.format(
            PREVIOUS_CONVERSATION_ORDER=previous_summary,
            USER_LEVEL=ct.CONVERSATION_USER_LEVEL[st.session_state.englv]
        )
    else:
        system_template = ct.SYSTEM_TEMPLATE_BASIC_CONVERSATION.format(
            PREVIOUS_CONVERSATION_ORDER="",
            USER_LEVEL=ct.CONVERSATION_USER_LEVEL[st.session_state.englv]
        )

    # 会話 Chain 作成
    st.session_state.chain_basic_conversation = ft.create_chain(
        system_template, 
        st.session_state.conversation_llm, 
        st.session_state.conversation_memory
    )

    # chat_history（直近5ターン＝最大10件）をメモリに再生
    for msg in user_memory.chat_history[-10:]:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            st.session_state.conversation_memory.chat_memory.add_user_message(content)
        elif role == "assistant":
            st.session_state.conversation_memory.chat_memory.add_ai_message(content)

    st.session_state.conversation_first_flg = False

def _handle_text_input_conversation(audio_input_text: str):
    """
    テキスト入力（チャット入力）からの会話処理
    """
    # ユーザー入力の表示
    with st.chat_message("user", avatar=ct.USER_ICON_PATH):
        st.markdown(audio_input_text)

    with st.spinner(ct.SPINNER_TTS_PREPARE):
        # LLMへ渡して回答取得
        llm_response = st.session_state.chain_basic_conversation.predict(input=audio_input_text)
        # TTS音声生成
        llm_response_audio = st.session_state.openai_obj.audio.speech.create(
            model=ct.AUDIO_MODEL,
            voice=ct.AUDIO_VOICE,
            input=llm_response,
            speed=st.session_state.speed
        )
        # 音声ファイル作成
        audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/{ct.AUDIO_OUTPUT_FILENAME_PREFIX}{int(time.time())}.wav"
        au.save_to_wav(llm_response_audio.content, audio_output_file_path)

    # 音声再生
    au.play_wav(audio_output_file_path)

    # AIメッセージ表示
    with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
        st.markdown(llm_response)

    # メッセージ履歴へ追加
    st.session_state.messages.append({"role": "user", "content": audio_input_text})
    st.session_state.messages.append({"role": "assistant", "content": llm_response})
    st.rerun()

def _handle_audio_input_conversation():
    """
    音声入力からの会話処理（録音→文字起こし→応答→読み上げ）
    """
    # 録音
    audio_input_file_path = f"{ct.AUDIO_INPUT_DIR}/{ct.AUDIO_INPUT_FILENAME_PREFIX}{int(time.time())}.wav"
    au.record_audio(audio_input_file_path)   

    # 文字起こし
    with st.spinner(ct.SPINNER_TRANSCRIBE):
        transcript = au.transcribe_audio(audio_input_file_path)
        audio_input_text = transcript.text

    # ユーザー入力表示
    with st.chat_message("user", avatar=ct.USER_ICON_PATH):
        st.markdown(audio_input_text)

    with st.spinner(ct.SPINNER_TTS_PREPARE):
        # LLMへ渡して回答取得
        llm_response = st.session_state.chain_basic_conversation.predict(input=audio_input_text)
        # TTS音声生成
        llm_response_audio = st.session_state.openai_obj.audio.speech.create(
            model=ct.AUDIO_MODEL,
            voice=ct.AUDIO_VOICE,
            input=llm_response,
            speed=st.session_state.speed
        )
        # 音声ファイル作成
        audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/{ct.AUDIO_OUTPUT_FILENAME_PREFIX}{int(time.time())}.wav"
        au.save_to_wav(llm_response_audio.content, audio_output_file_path)

    # 音声再生
    au.play_wav(audio_output_file_path)

    # AIメッセージ表示
    with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
        st.markdown(llm_response)

    # メッセージ履歴へ追加
    st.session_state.messages.append({"role": "user", "content": audio_input_text})
    st.session_state.messages.append({"role": "assistant", "content": llm_response})
    st.rerun()

def run_conversation_mode():
    """
    日常英会話モードのメイン処理
    - 初回準備（チェーン作成・履歴再生）
    - チャット入力優先
    - 音声入力時の処理
    """
    # 初回準備
    _prepare_conversation_chain_if_needed()

    # チャット入力優先
    if st.session_state.chat_message:
        audio_input_text = st.session_state.chat_message
        st.session_state.chat_message = ""
        _handle_text_input_conversation(audio_input_text)
        return

    # 音声入力
    _handle_audio_input_conversation()
