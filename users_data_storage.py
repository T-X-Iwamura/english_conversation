# users_data.py
import os
import json
import requests
import logging
from constants import Constants as ct
from user_memory import UserMemory


# JSONBin URL & Headers
JSONBIN_URL = f"{ct.JSONBIN_URL}{os.environ['JSONBIN_BIN_ID']}"
JSONBIN_HEADERS = {
    "Content-Type": "application/json",
    "X-MASTER-KEY": os.environ["JSONBIN_X_MASTER_KEY"]
}


# ============================================================
# ▼ UserMemory を保存（全ユーザーの record を更新）
# ============================================================
def save_user_memory(user_name: str, user_memory: UserMemory) -> bool:
    """
    UserMemory を JSONBin に保存する。
    record 全体（全ユーザー分）を書き換える。
    """
    logger = logging.getLogger(ct.LOGGER_NAME)

    # 現在のデータを取得
    all_users = _load_all_users()
    if not isinstance(all_users, dict):
        all_users = {}

    # 指定ユーザー分を更新
    all_users[user_name] = user_memory.to_dict()

    # JSONBin へ保存（PUT）
    try:
        response = requests.put(
            JSONBIN_URL,
            headers=JSONBIN_HEADERS,
            data=json.dumps(all_users, ensure_ascii=False)
        )
        response.raise_for_status()
        return True

    except Exception as e:
        logger.error(f"Failed to save user memory to JSONBin: {e}")
        return False


# ============================================================
# ▼ UserMemory を読み込み
# ============================================================
def load_user_memory(user_name: str) -> UserMemory:
    """
    指定ユーザーの UserMemory を JSONBin から読み出す。
    データが存在しなければ空の UserMemory を返す。
    """
    all_users = _load_all_users()

    if isinstance(all_users, dict) and user_name in all_users:
        user_data_dict = all_users[user_name]
        return UserMemory.from_dict(user_data_dict)

    # ユーザーがまだ存在しない場合 → 新規レコードとして扱う
    return UserMemory()


# ============================================================
# ▼ JSONBin record 全体を読み込み
# ============================================================
def _load_all_users() -> dict:
    """
    JSONBin から record を読み出し dict を返す。
    エラー時は空 dict。
    """
    logger = logging.getLogger(ct.LOGGER_NAME)

    try:
        response = requests.get(JSONBIN_URL, headers=JSONBIN_HEADERS)
        response.raise_for_status()

        json_data = response.json()
        record = json_data.get("record", {})

        if isinstance(record, dict):
            return record
        else:
            logger.warning("JSONBin record is not a dict. Resetting to empty dict.")
            return {}

    except Exception as e:
        logger.error(f"Failed to load users data from JSONBin: {e}")
        return {}
