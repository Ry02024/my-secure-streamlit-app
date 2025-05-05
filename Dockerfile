# ベースイメージを選択
FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピーしてインストール
COPY requirements.txt ./
# google-cloud-secret-manager もインストールされる
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY ./app /app/app
COPY .streamlit /.streamlit

# Streamlit が使用するポートを公開 (Cloud Run用に8080)
EXPOSE 8080

# ヘルスチェック (ポートを8080に)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# アプリケーションを実行 (-m オプションを使用、ポートを8080に)
CMD ["python", "-m", "streamlit", "run", "/app/app/main.py", "--server.port=8080", "--server.headless=true"]
