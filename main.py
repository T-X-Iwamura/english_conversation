import os
import streamlit as st
import initialize_util as iu

# 依存モジュールを読み込む前に、環境変数の読み込みと PATH(bin) の設定をセッション内で一度だけ実施
iu.initialize_environment_and_path()

# UIユーティリティの読み込み（環境初期化後）
import ui_util as uu

import time
import logging
import json
import functions as ft
import audio_util as au
import users_data_storage as ud
from constants import Constants as ct
from user_memory import UserMemory
import dictation_mode as dm
import conversation_mode as cm
import shadowing_mode as sm

# 各種設定（ページ設定・壁紙・タイトル画像の表示）
iu.setup_page_with_wallpaper_and_title()

# 初期処理（ログ/セッション状態/モデルなど）
iu.initialize_logger()
iu.initialize_session_state()

# サイドバーの描画（従来の with st.sidebar: ブロックを関数呼び出しに置き換え）
uu.render_sidebar()

# メインウィンドウの描画（案内メッセージとメッセージ一覧の表示を関数呼び出しに置き換え）
uu.render_main_window()


st.session_state.chat_message = st.chat_input()

# 「英会話開始」ボタンが押された場合の処理（以降は従来通り）
if st.session_state.start_flg:

    # モード：「ディクテーション」
    # 「ディクテーション」ボタン押下時か、「英会話開始」ボタン押下時か、チャット送信時
    if st.session_state.mode == ct.MODE_3 and (st.session_state.dictation_button_flg or st.session_state.dictation_count == 0 or st.session_state.chat_message):
        dm.run_dictation_mode()
    
    # モード：「日常英会話」
    elif st.session_state.mode == ct.MODE_1:
        cm.run_conversation_mode()
        
    # モード：「シャドーイング」
    elif st.session_state.mode == ct.MODE_2 and (st.session_state.shadowing_button_flg or st.session_state.shadowing_count == 0 or st.session_state.shadowing_audio_input_flg):
        sm.run_shadowing_mode()
