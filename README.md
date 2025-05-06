# セキュアチャットアプリケーション

Streamlit + Cloud Functions + Firestore + Google Login を使用したチャットアプリ。

## セットアップ

1.  GCP/Firebase プロジェクトの準備
2.  必要なAPIの有効化、サービスアカウントの作成、WIFの設定など (GCP設定スクリプトやコマンド群を実行)
3.  OAuth クライアント ID/Secret の作成と Secret Manager への登録
4.  Cookie 用の Secret の Secret Manager への登録
5.  `cloud_functions/chat_api/.env.yaml` の `PROJECT_NUMBER` を確認 (スクリプトで自動入力されるはず)
6.  `firebase deploy --only firestore:rules` で Firestore ルールをデプロイ
7.  `gcloud functions deploy ...` で Cloud Function をデプロイ (HTTPS URL を控える)
8.  `.github/workflows/deploy.yml` を編集 (WIF設定、Function URLなど、プレースホルダーを置き換える)
9.  コードを Git で管理し、GitHub に push して Cloud Run にデプロイ

## ローカルテスト

1.  `pip install -r streamlit_app/requirements.txt`
2.  `streamlit_app/config.yaml` にローカルテスト用の OAuth 情報を入力 (コメント解除して入力)
3.  (オプション) Firestore Emulator を起動 (`firebase emulators:start --only firestore`)
4.  (オプション) Cloud Functions Emulator を起動 (Functions Framework を使用)
5.  必要な環境変数を設定 (e.g., `CHAT_API_FUNCTION_URL` にローカルEmulatorのURLを設定)
6.  `python -m streamlit run streamlit_app/main.py` を実行

## 注意点

*   Cloud Functions との連携は、`streamlit-authenticator` がログイン後に ID トークンを `st.session_state` に保存することを前提としています。動作しない場合は `streamlit_app/core/api_client.py` の `get_id_token` 関数内のキー取得ロジックを修正する必要があります。
