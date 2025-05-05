from google.cloud import firestore
import os
import logging

# Cloud Run 環境では自動的にサービスアカウントが使われる
# ローカルテスト(Emulator)用に環境変数を確認する処理を追加しても良い
try:
    # GAE_RUNTIME 環境変数は Cloud Run/App Engine で設定される
    # FIRESTORE_EMULATOR_HOST 環境変数はエミュレータ利用時に設定
    if os.getenv('GAE_RUNTIME', '') == '' and os.getenv('FIRESTORE_EMULATOR_HOST', '') == '':
         logging.warning("本番環境でもエミュレータ環境でもないようです。Firestoreクライアントの初期化をスキップします。")
         # ローカル開発で認証情報ファイルを使う場合などはここで設定
         # from google.oauth2 import service_account
         # credentials = service_account.Credentials.from_service_account_file('path/to/key.json')
         # db = firestore.Client(credentials=credentials)
         db = None # または適切な初期化
    else:
         logging.info("Initializing Firestore Client...")
         db = firestore.Client()

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
            'timestamp': firestore.SERVER_TIMESTAMP # サーバー側のタイムスタンプ
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
