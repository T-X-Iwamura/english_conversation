# English Conversation

英語会話の練習を支援する Python アプリケーションです。プロンプトに応じて会話シナリオを生成し、対話形式で練習できます。

## 特長
- 会話シナリオの自動生成
- ロールプレイ（店員・客など）の切り替え
- 難易度・話題・語彙レベルの調整
- セッションログの保存（任意）

## 前提条件
- Python 3.9 以上
- pip または venv

## インストール
```bash
# 仮想環境の作成（任意）
python -m venv .venv
# 有効化
# Windows:
.venv\Scripts\activate
# 依存関係のインストール
pip install -r requirements.txt
```

## 使い方
```bash
# 基本的な実行
python main.py

# 話題や難易度の指定例
python main.py --topic "Travel" --level "B1" --role "shop_clerk"
```
- 起動後、画面指示に従ってユーザー発話を入力します。
- 応答は英語中心ですが、補助説明を日本語で表示するモードも設定可能です（設定項目参照）。

## 設定
- `--topic`: 会話の話題（例: Travel, Restaurant, Business）
- `--level`: 難易度（例: A2, B1, B2, C1）
- `--role`: ロールプレイの役割（例: customer, shop_clerk, interviewer）
- `--log`: セッションログ保存の有効化（例: `--log session1.txt`）

## 実行例
```text
You: Hi, I'd like to buy a train ticket to Oxford.
App: Sure! One-way or return? When would you like to travel?
You: One-way, this afternoon.
App: Great. Economy class is £18. Would you like to proceed?
```

## フォルダ構成（例）
```
english_conversation/
  ├─ main.py
  ├─ requirements.txt
  ├─ configs/
  ├─ data/
  └─ README.md
```

