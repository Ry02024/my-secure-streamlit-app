import streamlit as st
from app import firestore_client # Firestore連携モジュール
import logging
import os
import json
# Firebase Authentication 連携ライブラリをインポート (仮名)
try:
    # 例: pip install streamlit-firebase-auth を想定
    from streamlit_firebase_auth import FirebaseAuth
    firebase_auth_available = True
except ImportError:
    firebase_auth_available = False
    logging.warning("streamlit-firebase-auth library not found. Authentication functionality disabled.")
# Secret Manager クライアントライブラリ (必要であれば)
try:
    from google.cloud import secretmanager
    secretmanager_available = True
except ImportError:
    secretmanager_available = False
    logging.warning("google-cloud-secret-manager not installed. Secret Manager functionality might be limited.")


logging.basicConfig(level=logging.INFO)

st.set_page_config(layout="wide")

st.title("アイデア投稿・閲覧アプリ") # タイトルをシンプルに

# --- Firebase Authentication の設定と初期化 ---
auth = None
user_info = None # ログインユーザー情報格納用

if not firebase_auth_available:
    st.error("認証ライブラリが見つかりません。管理者に連絡してください。")
    st.stop() # アプリケーションを停止

# 環境変数から Firebase Web 設定を読み込む (JSON 文字列形式を想定)
firebase_config_json = os.getenv("FIREBASE_CONFIG_JSON", "{}")
try:
    firebase_config = json.loads(firebase_config_json)
    if not firebase_config: # 空のJSONでないかチェック
        st.error("Firebase 設定が環境変数に設定されていません。")
        st.stop()
    # Firebase Auth ライブラリを初期化
    auth = FirebaseAuth(firebase_config) # ライブラリの初期化メソッドに合わせる
except json.JSONDecodeError:
    st.error("Firebase 設定 (JSON) の形式が無効です。")
    st.stop()
except Exception as e:
    st.error(f"Firebase Auth の初期化に失敗しました: {e}")
    st.stop()


# --- ログインウィジェットを表示 ---
# login_widget() はログイン状態ならユーザー情報、未ログインならNoneを返す想定
if auth:
    user_info = auth.login_widget() # ライブラリのログインUI/状態チェックメソッド

# --- サイドバー: ログイン情報と Secret Manager (Secret Manager は参考) ---
st.sidebar.header("ユーザー情報")
if user_info:
    st.sidebar.write(f"名前: {user_info.get('displayName', 'N/A')}")
    st.sidebar.write(f"Email: {user_info.get('email', 'N/A')}")
    # st.sidebar.write(f"UID: {user_info.get('uid')}") # デバッグ用にUID表示
    if st.sidebar.button("ログアウト"):
        auth.logout() # ライブラリのログアウトメソッド
        st.rerun() # ログアウト後に再描画
else:
    st.sidebar.info("ログインしていません。")


# --- (参考) Secret Manager 取得ロジック (ログイン時のみ実行可能にする等も検討可) ---
# (内容は前回と同様、必要に応じて修正)
@st.cache_data
def get_secret(project_id, secret_id, version_id="latest"):
    # ... (get_secret 関数の定義は省略 - 前回と同じ) ...
    """Secret Managerからシークレットを取得する"""
    if not secretmanager_available:
        logging.warning("Secret Manager client library not available.")
        return None
    try:
        # Cloud Run環境ではサービスアカウント認証が使われる
        client = secretmanager.ServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        logging.info(f"Secret '{secret_id}' version '{version_id}' accessed successfully.")
        return payload
    except Exception as e:
        logging.error(f"Failed to access secret {secret_id}: {e}")
        return None

GCP_PROJECT_ID = os.getenv("GCP_PROJECT")
SECRET_ID_TO_FETCH = os.getenv("MY_APP_API_KEY_SECRET_ID", "my-app-api-key")
api_key_value = "未取得/未ログイン/環境外"

if user_info and os.getenv('GAE_RUNTIME', '') != '': # ログイン済みかつCloud Run環境
     if GCP_PROJECT_ID and secretmanager_available:
        fetched_secret = get_secret(GCP_PROJECT_ID, SECRET_ID_TO_FETCH)
        api_key_value = fetched_secret if fetched_secret else "Secret取得失敗"
     elif not GCP_PROJECT_ID:
         api_key_value = "プロジェクトID未設定"
     else:
         api_key_value = "Secret Manager利用不可"

st.sidebar.subheader("Secret Manager の値:")
st.sidebar.text_input("取得した Secret の値", value=api_key_value, type="password", disabled=True)
st.sidebar.caption(f"(取得元 Secret ID: {SECRET_ID_TO_FETCH})")


# --- メインコンテンツ (ログイン時のみ表示) ---
if user_info:
    # ログイン済みの場合、メインのアプリ機能を表示
    col1, col2 = st.columns(2)

    with col1:
        st.header("新しいアイデアを投稿")
        with st.form("idea_form", clear_on_submit=True):
            idea_title = st.text_input("アイデアのタイトル")
            idea_description = st.text_area("アイデアの説明", height=150)
            submitted = st.form_submit_button("投稿する")
            if submitted:
                if idea_title and idea_description:
                    # ★★★ 投稿時にユーザーIDを渡す ★★★
                    user_uid = user_info.get('uid') # ライブラリが返すユーザーIDのキー名に合わせる
                    if user_uid:
                        # firestore_client.add_idea を修正して user_id を受け取るようにする
                        result_id = firestore_client.add_idea(idea_title, idea_description, user_uid)
                        if result_id:
                            st.success(f"アイデアを投稿しました！")
                        else:
                            st.error("アイデアの投稿に失敗しました。")
                    else:
                        st.error("ユーザーIDが取得できませんでした。")
                else:
                    st.warning("タイトルと説明を入力してください。")

    with col2:
        st.header("投稿されたアイデア一覧")
        # ★★★ 必要であれば自分のアイデアのみ表示するよう get_ideas を修正 ★★★
        # ideas = firestore_client.get_ideas(user_info.get('uid'))
        ideas = firestore_client.get_ideas() # まずは全員分表示

        if not ideas:
            st.info("まだアイデアは投稿されていません。")
        else:
            container = st.container(height=500)
            with container:
                for idea in ideas:
                    # 投稿者情報を表示するなどの拡張も可能
                    # author_id = idea.get('userId')
                    with st.expander(f"{idea.get('title', 'タイトルなし')}"):
                        st.write(f"**説明:**")
                        st.markdown(f"```\n{idea.get('description', '説明なし')}\n```")
                        ts = idea.get('timestamp')
                        if ts and hasattr(ts, 'strftime'):
                             st.caption(f"投稿日時 (UTC): {ts.strftime('%Y-%m-%d %H:%M:%S')}")

else:
    # 未ログインの場合のメッセージ
    st.info("Google アカウントでログインしてください。")
    # ログインボタンは auth.login_widget() が表示する想定