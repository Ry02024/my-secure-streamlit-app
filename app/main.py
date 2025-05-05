import streamlit as st
from app import firestore_client
import logging
import os # Secret Manager用にosをインポート

logging.basicConfig(level=logging.INFO)

st.set_page_config(layout="wide") # 横幅を広く使う設定

st.title("アイデア投稿・閲覧アプリ")

# --- (オプション) Secret Managerから値を取得して表示 ---
# この部分はCloud Runデプロイ後に意味を持つ。ローカル(Emulator)ではSECRET_IDがない場合エラーになる可能性あり。
# SECRET_ID = "my-app-api-key" # GitHub Actionsから環境変数として渡すことを想定
# api_key_value = "取得できませんでした"
# try:
#     # Secret Manager クライアントを初期化 (Cloud Runでは自動認証)
#     from google.cloud import secretmanager
#     if os.getenv('GAE_RUNTIME', '') != '': # Cloud Run環境でのみ実行試行
#         client = secretmanager.SecretManagerServiceClient()
#         # 環境変数 PROJECT_ID が必要 (Cloud Runでは自動設定されることが多い)
#         project_id = os.getenv("PROJECT_ID", None)
#         if project_id:
#              name = f"projects/{project_id}/secrets/{SECRET_ID}/versions/latest"
#              response = client.access_secret_version(request={"name": name})
#              api_key_value = response.payload.data.decode("UTF-8")
#              logging.info(f"Secret '{SECRET_ID}' を取得しました。")
#         else:
#              logging.warning("環境変数 PROJECT_ID が設定されていません。Secretを取得できません。")
#     else:
#         logging.info("Cloud Run環境ではないため、Secret Managerからの取得をスキップします。")

# except Exception as e:
#     logging.error(f"Secret Managerからのシークレット取得中にエラー: {e}")

# st.sidebar.subheader("Secret Managerの値:")
# st.sidebar.text_input("取得したAPIキー (例)", value=api_key_value, type="password", disabled=True)
# st.sidebar.caption(f"(取得元: {SECRET_ID})")

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
                    # clear_on_submit=True なので rerun は不要かも
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
        # 見た目を少し改善
        container = st.container(height=500) # 高さを指定してスクロール可能に
        with container:
            for idea in ideas:
                with st.expander(f"{idea.get('title', 'タイトルなし')}"):
                    st.write(f"**説明:**")
                    st.markdown(f"```\n{idea.get('description', '説明なし')}\n```") # Markdownで表示
                    # タイムスタンプが存在し、datetimeオブジェクトなら表示
                    ts = idea.get('timestamp')
                    if ts and hasattr(ts, 'strftime'):
                         # 日本時間に変換する場合 (pytzが必要になるかも)
                         # jst = ts + timedelta(hours=9)
                         # st.caption(f"投稿日時: {jst.strftime('%Y-%m-%d %H:%M:%S')} JST")
                         st.caption(f"投稿日時 (UTC): {ts.strftime('%Y-%m-%d %H:%M:%S')}")
                    # st.caption(f"ID: {idea.get('id', 'N/A')}") # IDはデバッグ時以外は不要かも

