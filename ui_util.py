import streamlit as st
import logging
import json
import functions as ft
import users_data_storage as ud
from constants import Constants as ct
from user_memory import UserMemory
import user_memory_manager as um

def render_sidebar():
    """
    サイドバーの描画とボタン操作・状態更新を行う
    """
    with st.sidebar:
        st.markdown(ct.SETTINGS_SIDEBAR_TITLE)
        
        st.markdown(ct.SETTINGS_SIDEBAR_USER_NAME)
        st.session_state.user_name = st.text_input(
            "ユーザー名",
            value="",
            max_chars=ct.MAX_USER_NAME_LENGTH,
            help=ct.USERS_NAME_INPUT_HELP,
            label_visibility="collapsed"
        )

        st.markdown(ct.SETTINGS_SIDEBAR_MODE)
        st.session_state.mode = st.selectbox(
            label=ct.MODE_LABEL,
            options=[ct.MODE_1, ct.MODE_2, ct.MODE_3],
            label_visibility="collapsed"
        )
        # モードを変更した際の処理
        if st.session_state.mode != st.session_state.pre_mode:
            # 自動でそのモードの処理が実行されないようにする
            st.session_state.start_flg = False
            # 「日常英会話」選択時の初期化処理
            st.session_state.conversation_first_flg = True
            if st.session_state.mode == ct.MODE_1:
                st.session_state.dictation_flg = False
                st.session_state.shadowing_flg = False
            # 「シャドーイング」選択時の初期化処理
            st.session_state.shadowing_count = 0
            st.session_state.shadowing_first_flg = True
            if st.session_state.mode == ct.MODE_2:
                st.session_state.dictation_flg = False
            # 「ディクテーション」選択時の初期化処理
            st.session_state.dictation_count = 0
            st.session_state.dictation_first_flg = True
            if st.session_state.mode == ct.MODE_3:
                st.session_state.shadowing_flg = False
            # チャット入力欄を非表示にする
            st.session_state.chat_open_flg = False
            st.session_state.chat_message = ""
            # モード変更後は一旦メッセージをクリアする
            st.session_state.messages = []
        
            need_rerun = (st.session_state.mode != "")
            st.session_state.pre_mode = st.session_state.mode
            if need_rerun:
                st.rerun()

        st.markdown(ct.SETTINGS_SIDEBAR_ENGLISH_LEVEL)
        st.session_state.englv = st.selectbox(
            label=ct.ENGLISH_LEVEL_LABEL,
            options=ct.ENGLISH_LEVEL_OPTION,
            label_visibility="collapsed"
        )

        st.markdown(ct.SETTINGS_SIDEBAR_SPEED)
        st.session_state.speed = st.selectbox(
            label=ct.SPEED_LABEL,
            options=ct.PLAY_SPEED_OPTION,
            index=ct.PLAY_SPEED_DEFAULT_INDEX,
            label_visibility="collapsed"
        )

        if st.session_state.start_flg:
            st.button(ct.START_BUTTON_LABEL, type="primary")
        else:
            st.session_state.start_flg = st.button(ct.START_BUTTON_LABEL, type="primary")

        st.divider()
        
        # ▼ ユーザーデータ保存ボタン
        if st.button(ct.SAVE_USERS_DATA_BUTTON_LABEL, type="primary", key="save_user_data_btn"):
            st.session_state.save_user_data_confirm_open = True
        
        # ▼ 保存確認ダイアログと保存処理
        if st.session_state.get("save_user_data_confirm_open"):
            # ユーザーデータ保存ボタン押下時の処理       
            if st.session_state.user_name == "":
                st.write(ct.SAVE_USERS_DATA_NO_USER)
                st.session_state.save_user_data_confirm_open = False
                
            else:    
                st.write(ct.SAVE_USERS_DATA_CONFIRMATION)
                col_ok, col_cancel = st.columns(2)

                # OK ボタン
                with col_ok:
                    if st.button(ct.SAVE_USERS_DATA_OK_LABEL, key="confirm_ok"):
                        # ユーザーデータ保存の重処理を関数に委譲
                        with st.spinner(ct.SAVING_USER_DATA):
                            um.perform_user_memory_save()
                        st.session_state.save_user_data_confirm_open = False
                        st.rerun()

                # キャンセルボタン
                with col_cancel:
                    if st.button(ct.SAVE_USERS_DATA_CANCEL_LABEL, key="confirm_cancel"):
                        st.session_state.save_user_data_confirm_open = False
                        st.rerun()
    
        st.divider()
        
        # 操作説明
        st.markdown("**【操作説明】**")
        st.success("""
        - モードと再生速度を選択し、「英会話開始」ボタンを押して英会話を始めましょう。
        - モードは「日常英会話」「シャドーイング」「ディクテーション」から選べます。
        - 発話後、5秒間沈黙することで音声入力が完了します。
        - 「一時中断」ボタンを押すことで、英会話を一時中断できます。
        """)

def render_main_window():
    """
    メインウィンドウの初期表示（案内メッセージ）とメッセージ一覧の描画
    """
    # 案内メッセージの表示
    with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
        st.markdown("こちらは生成AIによる音声英会話の練習アプリです。何度も繰り返し練習し、英語力をアップさせましょう。")

    st.divider()

    # メッセージリストの一覧表示
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message(message["role"], avatar=ct.AI_ICON_PATH):
                st.markdown(message["content"])
        elif message["role"] == "user":
            with st.chat_message(message["role"], avatar=ct.USER_ICON_PATH):
                st.markdown(message["content"])
        else:
            st.divider()

    # LLMレスポンスの下部にモード実行のボタン表示
    if st.session_state.shadowing_flg:
        st.session_state.shadowing_button_flg = st.button(ct.SHADOWING_BUTTON_LABEL)
    if st.session_state.dictation_flg:
        st.session_state.dictation_button_flg = st.button(ct.DICTATION_BUTTON_LABEL)

    # 「ディクテーション」モードのチャット入力受付時に実行
    if st.session_state.chat_open_flg:
        st.info(ct.DICTATION_INFO_MESSAGE)