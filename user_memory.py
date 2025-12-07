# UserMemory.py

class UserMemory:
    """
    ユーザーごとの記憶情報をまとめて保持するクラス。
    profile / long_memory / summary / chat_history の4つを扱う。

    - profile       : 安定的な個人情報（名前・年齢・性別など）
    - long_memory   : 長期的に保持すべき情報（学習目標・好みなど）
    - summary       : 直近の会話の短期要約
    - chat_history  : 直近5ターン（最大10件）分の会話履歴
    """

    def __init__(self, profile=None, long_memory=None, summary="", chat_history=None):
        # 安定情報
        self.profile = profile or {}

        # 長期記憶（AIが継続的に利用できる事実）
        self.long_memory = long_memory or []

        # 最新サマリー
        self.summary = summary

        # 会話履歴（最大10件）
        self.chat_history = chat_history or []

    # ------------------------------------------------------------
    # dict から UserMemory オブジェクトを復元
    # ------------------------------------------------------------
    @staticmethod
    def from_dict(data: dict):
        if not isinstance(data, dict):
            data = {}

        return UserMemory(
            profile=data.get("profile", {}),
            long_memory=data.get("long_memory", []),
            summary=data.get("summary", ""),
            chat_history=data.get("chat_history", []),
        )

    # ------------------------------------------------------------
    # UserMemory を保存用 dict に変換
    # ------------------------------------------------------------
    def to_dict(self):
        """
        JSONBin に保存する形式に変換する。
        chat_history は常に 10 件（5ターン）に制限。
        """
        sanitized_history = self._sanitize_chat_history(self.chat_history)

        return {
            "profile": self.profile,
            "long_memory": self.long_memory,
            "summary": self.summary,
            "chat_history": sanitized_history[-10:],
        }

    # ------------------------------------------------------------
    # chat_history の形式を整える（将来の拡張に備えて）
    # ------------------------------------------------------------
    @staticmethod
    def _sanitize_chat_history(history):
        """
        history は以下形式を想定：
        {
            "role": "user" | "assistant",
            "content": "..."
        }
        """
        if not isinstance(history, list):
            return []

        valid_items = []
        for item in history:
            if not isinstance(item, dict):
                continue
            if "role" not in item or "content" not in item:
                continue
            if item["role"] not in ["user", "assistant"]:
                continue
            valid_items.append(item)

        return valid_items
