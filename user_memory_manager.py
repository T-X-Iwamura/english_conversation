import streamlit as st
import logging
import json
from constants import Constants as ct
import functions as ft
import users_data_storage as ud
from user_memory import UserMemory

def _create_conversation_summary(user_memory: UserMemory) -> str:
    """
    既存メモリと直近履歴から会話サマリーを生成
    """
    summary_system_template = ct.SYSTEM_TEMPLATE_CREATE_CONVERSATION_SUMMARY.format(
        PROFILE_TEXT=json.dumps(user_memory.profile, ensure_ascii=False),
        LONG_MEMORY_TEXT=json.dumps(user_memory.long_memory, ensure_ascii=False),
        PREVIOUS_SUMMARY_TEXT=user_memory.summary,
        CHAT_HISTORY_TEXT=json.dumps(user_memory.chat_history, ensure_ascii=False),
    )
    summary_chain = ft.create_chain(
        summary_system_template,
        st.session_state.conversation_llm,
        st.session_state.conversation_memory
    )
    return summary_chain.predict(input="")

def _extract_profile(conversation_summary: str) -> dict:
    """
    会話サマリーと直近履歴からユーザープロファイルを抽出（JSON想定）
    """
    system_template = ct.SYSTEM_TEMPLATE_EXTRACT_PROFILE.format(
        LATEST_SUMMARY_TEXT=conversation_summary,
        RECENT_CHAT_HISTORY_TEXT=json.dumps(st.session_state.messages[-10:], ensure_ascii=False),
    )
    chain = ft.create_chain(
        system_template,
        st.session_state.conversation_llm,
        st.session_state.conversation_memory
    )
    text = chain.predict(input="")
    try:
        return json.loads(text) if text else {}
    except Exception:
        return {}

def _merge_profile(base_profile: dict, extracted_profile: dict) -> dict:
    """
    既存プロファイルと抽出プロファイルをマージ（null/空は上書きしない）
    """
    merged = base_profile.copy()
    if isinstance(extracted_profile, dict):
        for key, value in extracted_profile.items():
            if value not in [None, "", [], "null"]:
                merged[key] = value
    return merged

def _latest_history() -> list:
    """
    直近のチャット履歴（最大10件＝5ターンぶん）
    """
    return st.session_state.messages[-10:]

def _extract_long_memory(user_memory: UserMemory, conversation_summary: str, latest_history: list) -> list:
    """
    長期記憶の抽出と既存への統合（重複排除）
    """
    system_template = ct.SYSTEM_TEMPLATE_EXTRACT_LONG_MEMORY.format(
        LATEST_SUMMARY_TEXT=conversation_summary,
        RECENT_CHAT_HISTORY_TEXT=json.dumps(latest_history, ensure_ascii=False),
        EXISTING_LONG_MEMORY=json.dumps(user_memory.long_memory, ensure_ascii=False),
    )
    chain = ft.create_chain(
        system_template,
        st.session_state.conversation_llm,
        st.session_state.conversation_memory
    )
    text = chain.predict(input="")
    try:
        extracted = json.loads(text)
    except Exception:
        extracted = {"new_memory": []}

    new_items = extracted.get("new_memory", [])
    updated = user_memory.long_memory.copy()
    for item in new_items:
        if item not in updated:
            updated.append(item)
    return updated

def _maybe_compress_long_memory(long_memory_list: list) -> list:
    """
    長期記憶が多い場合に圧縮（LLM要約・統合）
    """
    if len(long_memory_list) <= 8:
        return long_memory_list

    system_template = ct.SYSTEM_TEMPLATE_COMPRESS_LONG_MEMORY.format(
        LONG_MEMORY_TEXT=json.dumps(long_memory_list, ensure_ascii=False)
    )
    chain = ft.create_chain(
        system_template,
        st.session_state.conversation_llm,
        st.session_state.conversation_memory
    )
    text = chain.predict(input="")
    try:
        result = json.loads(text)
        compressed = result.get("compressed_memory", [])
        if isinstance(compressed, list) and len(compressed) > 0:
            return compressed
    except Exception:
        pass
    return long_memory_list

def _fix_memory_contradictions(merged_profile: dict, long_memory_list: list) -> list:
    """
    プロファイルと長期記憶の矛盾を修正（LLMで整合性を取る）
    """
    system_template = ct.SYSTEM_TEMPLATE_FIX_MEMORY_CONTRADICTIONS.format(
        PROFILE_TEXT=json.dumps(merged_profile, ensure_ascii=False),
        LONG_MEMORY_TEXT=json.dumps(long_memory_list, ensure_ascii=False)
    )
    chain = ft.create_chain(
        system_template,
        st.session_state.conversation_llm,
        st.session_state.conversation_memory
    )
    text = chain.predict(input="")
    try:
        result = json.loads(text)
        fixed_list = result.get("fixed_memory", [])
        if isinstance(fixed_list, list) and len(fixed_list) >= 0:
            return fixed_list
    except Exception:
        pass
    return long_memory_list

def _save_user_memory(merged_profile: dict, long_memory_list: list, conversation_summary: str, latest_history: list) -> None:
    """
    更新済みのユーザーメモリを保存
    """
    logger = logging.getLogger(ct.LOGGER_NAME)
    updated_user_memory = UserMemory(
        profile=merged_profile,
        long_memory=long_memory_list,
        summary=conversation_summary,
        chat_history=latest_history,
    )
    if ud.save_user_memory(st.session_state.user_name, updated_user_memory):
        logger.info("User memory (profile, summary, chat_history) saved successfully")

def perform_user_memory_save():
    """
    ユーザー名と現在のセッション状態に基づき、プロフィール・会話サマリー・長期記憶・直近履歴を更新し保存する
    """
    # 1) 既存メモリの読み込み
    user_memory = ud.load_user_memory(st.session_state.user_name)

    # 2) 会話サマリーの生成
    conversation_summary = _create_conversation_summary(user_memory)

    # 3) プロファイル抽出とマージ
    extracted_profile = _extract_profile(conversation_summary)
    merged_profile = _merge_profile(user_memory.profile, extracted_profile)

    # 4) 直近履歴の取得
    latest_history = _latest_history()

    # 5) 長期記憶の抽出と統合
    updated_long_memory = _extract_long_memory(user_memory, conversation_summary, latest_history)

    # 6) 長期記憶の圧縮（必要に応じて）
    updated_long_memory = _maybe_compress_long_memory(updated_long_memory)

    # 7) プロファイルとの矛盾修正
    updated_long_memory = _fix_memory_contradictions(merged_profile, updated_long_memory)

    # 8) 保存
    _save_user_memory(merged_profile, updated_long_memory, conversation_summary, latest_history)
