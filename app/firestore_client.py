from google.cloud import firestore
import os
import logging

# Cloud Run 環境では自動的にサービスアカウントが使われる
# ローカルテスト(Emulator)用に環境変数を確認する処理
try:
    if os.getenv('FIRESTORE_EMULATOR_HOST'):
        # エミュレータ利用時
        logging.info(f"Using Firestore Emulator at {os.getenv('FIRESTORE_EMULATOR_HOST')}")
        db = firestore.Client() # エミュレータ利用時も認証なしでClientを作成できる
    elif os.getenv('GAE_RUNTIME', '') != '':
        # Cloud Run/App Engine 環境 (本番想定)
        logging.info("Running in Cloud Run/GAE environment. Initializing Firestore Client with default credentials.")
        db = firestore.Client()
    else:
        # その他の環境（ローカルだがエミュレータ未使用、など）
        logging.warning("Not in Cloud Run/GAE or Emulator environment. Firestore client might not be initialized correctly.")
        # ここでローカルキーファイルでの認証など、別の初期化方法を検討できる
        db = None # 安全のためNoneにしておく

except Exception as e:
    logging.error(f"Firestore クライアントの初期化に失敗しました: {e}")
    db = None

IDEAS_COLLECTION = 'ideas'

def add_idea(title: str, description: str):
    """Firestoreにアイデアを追加"""
    if not db:
        logging.error("Firestore クライアントが利用できません。")
        return None
    if not title or not description: # 簡単なバリデーション
         logging.warning("タイトルまたは説明が空です。")
         return None
    try:
        doc_ref = db.collection(IDEAS_COLLECTION).document()
        doc_ref.set({
            'title': title,
            'description': description,
            'timestamp': firestore.SERVER_TIMESTAMP, # サーバー側のタイムスタンプ
            'userId': user_id # ★★★ ユーザーIDを追加 ★★★
        })
        logging.info(f"アイデアを追加しました: {doc_ref.id}")
        return doc_ref.id
    except Exception as e:
        logging.error(f"アイデアの追加中にエラーが発生しました: {e}")
        return None

def get_ideas():
    """Firestoreからアイデア一覧を取得"""
    if not db:
        logging.error("Firestore クライアントが利用できません。")
        return []
    try:
        ideas_ref = db.collection(IDEAS_COLLECTION).order_by(
            'timestamp', direction=firestore.Query.DESCENDING).limit(50) # 最新50件
        docs = ideas_ref.stream()
        ideas_list = [{'id': doc.id, **doc.to_dict()} for doc in docs]
        logging.info(f"{len(ideas_list)} 件のアイデアを取得しました。")
        return ideas_list
    except Exception as e:
        logging.error(f"アイデアの取得中にエラーが発生しました: {e}")
        return []
