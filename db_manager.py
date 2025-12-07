import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import logging
import requests
import users_data_storage as ud
import user_memory as UserMemory
import functions as ft
from constants import Constants as ct

JSONBIN_URL = f"{ct.JSONBIN_URL}{os.environ['JSONBIN_BIN_ID']}"
JSONBIN_HEADERS = {
    "Content-Type": "application/json",
    "X-MASTER-KEY": os.environ["JSONBIN_X_MASTER_KEY"]
}

# デバッグ用のDB操作UI

ft.initialize_logger()

st.header("【デバッグ用：ユーザーデータ操作】")

st.session_state.user_name = st.text_input("ユーザー名", value="", max_chars=ct.MAX_USER_NAME_LENGTH, help=ct.USERS_NAME_INPUT_HELP, label_visibility="collapsed")

st.divider()

if st.button("Show All User Data", type="primary"):
    if not st.session_state.user_name == "":
        all_users = ud._load_all_users()
        if isinstance(all_users, dict):
            for user_name, user_data in all_users.items():
                if user_name == st.session_state.user_name:
                    st.json(user_data)

if st.button("Clear Certain User Data", type="primary"):
    if not st.session_state.user_name == "":
        um = UserMemory.UserMemory()
        if ud.save_user_memory(st.session_state.user_name, um):
            st.success(f"User data for '{st.session_state.user_name}' cleared.")
        else:
            st.error(f"Failed to clear user data for '{st.session_state.user_name}'.")
