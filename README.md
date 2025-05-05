# Secure Streamlit Idea App

## 概要

このプロジェクトは、安全なクラウドネイティブアプリケーションの構築例を示すサンプルです。ユーザーがアイデアを投稿し、一覧表示できるシンプルな Web アプリケーションを、Python の Streamlit フレームワークを用いて開発します。バックエンドのデータベースには Google Cloud Firestore を使用し、アプリケーションは Google Cloud Run 上で動作します。

デプロイプロセスは GitHub Actions を使用して自動化されており、Google Cloud への認証には Workload Identity Federation (WIF) を利用することで、サービスアカウントキーを使わないセキュアな CI/CD を実現しています。

## 主な機能

*   Web UI (Streamlit) を介したアイデア（タイトルと説明）の投稿
*   Firestore に保存されたアイデアの一覧表示

## 技術スタック

*   **フロントエンド/アプリケーション:** Python, Streamlit
*   **データベース:** Google Cloud Firestore (Native Mode)
*   **ホスティング:** Google Cloud Run
*   **コンテナレジストリ:** Google Artifact Registry
*   **CI/CD:** GitHub Actions
*   **セキュア認証 (CI/CD):** Google Cloud Workload Identity Federation (WIF)
*   **インフラ定義:** Docker
*   **(開発環境):** GitHub Codespaces, Firebase Local Emulator Suite

## アーキテクチャ概要

```
[ユーザー] <--> [Streamlit App (Cloud Run)] <--> [Firestore Database]
                 ^                                  |
                 | (App Service Account)            | (Security Rules)
                 |                                  |
[GitHub Repo] ---> [GitHub Actions (CI/CD)] --------+
                 |    |
                 |    | (WIF Auth with Deploy SA)
                 |    v
                 |   [Artifact Registry] (Container Image)
                 |    |
                 +-----> [Deploy to Cloud Run]
```

1.  ユーザーは Cloud Run でホストされている Streamlit アプリにアクセスします。
2.  Streamlit アプリは、自身に紐付けられた Google Cloud サービスアカウント (`app-service-account`) を使用して、自動的に認証を行い Firestore と通信します。
3.  Firestore へのアクセスは、定義されたセキュリティルールによって制御されます。
4.  開発者が GitHub リポジトリの `main` ブランチにコードをプッシュすると、GitHub Actions がトリガーされます。
5.  GitHub Actions は Workload Identity Federation を使用して、デプロイ用のサービスアカウント (`deploy-service-account`) として一時的に Google Cloud に認証します（サービスアカウントキーは不要）。
6.  Actions は Docker イメージをビルドし、Artifact Registry にプッシュします。
7.  Actions は Artifact Registry のイメージを使用して、Cloud Run に新しいリビジョンをデプロイします。

## セットアップとローカル実行 (GitHub Codespaces 推奨)

1.  **Codespace の起動:**
    *   このリポジトリの GitHub ページで、「Code」ボタンをクリックし、「Codespaces」タブを選択します。
    *   「Create codespace on main」をクリックして Codespace を起動します。
    *   必要なツール (Python, Firebase CLI, Node.js) と依存関係 (`requirements.txt`) が自動的にインストールされます。
2.  **ターミナルを開く:** Codespace 内でターミナルを開きます。
3.  **Firebase エミュレータの起動:** 最初のターミナルで実行します。
    ```bash
    firebase emulators:start --only firestore
    ```
    Firestore エミュレータが `localhost:8080`、Emulator UI が `localhost:4000` で起動します。ポートは自動的に転送されます。
4.  **Streamlit アプリの起動:** 別のターミナルを開いて実行します (環境変数 `FIRESTORE_EMULATOR_HOST=localhost:8080` が `.env` または `devcontainer.json` 経由で設定されていることを確認)。
    ```bash
    streamlit run app/main.py
    ```
    Streamlit アプリが `localhost:8501` で起動し、ポートは自動的に転送されます。
5.  **アクセス:**
    *   VS Code の「ポート」タブから、転送されたポート (8501, 4000) をブラウザで開きます。
    *   Streamlit アプリで動作を確認し、Emulator UI で Firestore のデータを確認します。

## デプロイ

*   **自動デプロイ:** このリポジトリの `main` ブランチにコミットをプッシュすると、`.github/workflows/deploy.yml` で定義された GitHub Actions ワークフローが自動的に実行され、Cloud Run にデプロイされます。
*   **初回 Google Cloud 設定:**
    *   必要な Google Cloud API (Cloud Run, Firestore, Artifact Registry, IAM, STS など) を有効化する必要があります。
    *   `app-service-account` (Firestore アクセス用) と `deploy-service-account` (デプロイ用) の2つのサービスアカウントを作成し、適切な IAM ロールを付与する必要があります。
    *   GitHub Actions が `deploy-service-account` として認証できるよう、Workload Identity Federation プールとプロバイダを設定し、サービスアカウントに `roles/iam.workloadIdentityUser` を付与する必要があります。詳細はワークフローファイル (`deploy.yml`) の `env` セクションや Google Cloud のドキュメントを参照してください。
*   **Firestore ルールのデプロイ:** `firestore.rules` ファイルは別途デプロイが必要です。Firebase CLI を使うのが簡単です。
    ```bash
    # firebase login (初回)
    firebase use YOUR_PROJECT_ID
    firebase deploy --only firestore:rules
    ```

## セキュリティに関する考慮事項

*   **CI/CD セキュリティ:** Workload Identity Federation を使用し、GitHub Actions にサービスアカウントキーを渡す必要がありません。認証は短命な OIDC トークンに基づきます。
*   **アプリケーション認証:** Cloud Run アプリケーションは、紐付けられたサービスアカウントの認証情報を自動的に使用して Firestore にアクセスします。コード内に認証情報を埋め込む必要はありません。
*   **データアクセス制御:** Firestore セキュリティルール (`firestore.rules`) により、データベースへのアクセスを厳密に制御します。現状は認証済みアクセスのみ許可する基本的なルールですが、要件に応じて強化が必要です。
*   **依存関係管理:** GitHub の Dependabot が有効になっており、依存ライブラリの既知の脆弱性を検知します。定期的な確認とアップデートが推奨されます。
*   **(推奨) シークレット管理:** アプリケーションで API キーなどの機密情報が必要な場合は、Google Cloud Secret Manager を使用し、Cloud Run に安全にマウントしてください。

## 今後の改善点 (例)

*   **ユーザー認証:** Firebase Authentication などを導入し、ユーザーごとにデータの読み書き権限を制御する。
*   **Firestore ルールの強化:** データバリデーションやより詳細なアクセス制御ルールを追加する。
*   **エラーハンドリング:** より堅牢なエラーハンドリングとユーザーへのフィードバックを実装する。
*   **テスト:** 単体テストや結合テストを追加し、CI/CD パイプラインに組み込む。
*   **UI/UX の改善:** Streamlit の機能を活用して、より使いやすいインターフェースにする。

```
