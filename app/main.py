import streamlit as st
from app import firestore_client
import logging
import os
from google.cloud import secretmanager # Secret Manager用にインポート

logging.basicConfig(level=logging.INFO)

st.set_page_config(layout="wide")

st.title("アイデア投稿・閲覧アプリ (Cloud Run)") # タイトル変更

# --- Secret Managerから値を取得する関数 ---
# キャッシュを利用して毎回APIを叩かないようにする (@st.cache_data)
@st.cache_data # 結果をキャッシュ
def get_secret(project_id, secret_id, version_id="latest"):
    """Secret Managerからシークレットを取得する"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        logging.info(f"Secret '{secret_id}' version '{version_id}' accessed successfully.")
        return payload
    except Exception as e:
        logging.error(f"Failed to access secret {secret_id}: {e}")
        return None

# --- Secret Managerから値を取得して表示 ---
# Cloud Run環境で PROJECT_ID と SECRET_ID が環境変数として設定されている想定
GCP_PROJECT_ID = os.getenv("GCP_PROJECT") # Cloud Run では GCP_PROJECT が設定されることが多い
SECRET_ID_TO_FETCH = os.getenv("MY_APP_API_KEY_SECRET_ID", "my-app-api-key") # 環境変数でSecret IDを指定可能に
api_key_value = "取得失敗 or 未設定"

# GCP_PROJECT_ID が取得できた場合のみ実行
if GCP_PROJECT_ID:
    logging.info(f"Attempting to fetch secret '{SECRET_ID_TO_FETCH}' from project '{GCP_PROJECT_ID}'")
    fetched_secret = get_secret(GCP_PROJECT_ID, SECRET_ID_TO_FETCH)
    if fetched_secret:
        api_key_value = fetched_secret
    else:
        api_key_value = "Secret取得失敗"
else:
    logging.warning("GCP_PROJECT environment variable not found. Skipping Secret Manager fetch.")
    api_key_value = "プロジェクトID未設定"

# サイドバーに表示
st.sidebar.subheader("Secret Manager の値:")
st.sidebar.text_input("取得した Secret の値", value=api_key_value, type="password", disabled=True)
st.sidebar.caption(f"(取得元 Secret ID: {SECRET_ID_TO_FETCH})")


# --- レイアウト調整 (2カラム) ---
col1, col2 = st.columns(2)

with col1:
    # --- アイデア投稿フォーム ---
    st.header("新しいアイデアを投稿")
    with st.form("idea_form", clear_on_submit=True):
        idea_title = st.text_input("アイデアのタイトル")
        idea_description = st.text_area("アイデアの説明", height=150)
        submitted = st.form_submit_button("投稿する")
        if submitted:
            if idea_title and idea_description:
                result_id = firestore_client.add_idea(idea_title, idea_description)
                if result_id:
                    st.success(f"アイデアを投稿しました！")
                else:
                    st.error("アイデアの投稿に失敗しました。")
            else:
                st.warning("タイトルと説明を入力してください。")

with col2:
    # --- アイデア一覧表示 ---
    st.header("投稿されたアイデア一覧")
    ideas = firestore_client.get_ideas()

    if not ideas:
        st.info("まだアイデアは投稿されていません。")
    else:
        container = st.container(height=500)
        with container:
            for idea in ideas:
                with st.expander(f"{idea.get('title', 'タイトルなし')}"):
                    st.write(f"**説明:**")
                    st.markdown(f"```\n{idea.get('description', '説明なし')}\n```")
                    ts = idea.get('timestamp')
                    if ts and hasattr(ts, 'strftime'):
                         st.caption(f"投稿日時 (UTC): {ts.strftime('%Y-%m-%d %H:%M:%S')}")

