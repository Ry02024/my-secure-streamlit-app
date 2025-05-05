# ベースイメージを選択
FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピーしてインストール
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY ./app /app/app
COPY .streamlit /.streamlit

# Streamlit が使用するポートを公開
EXPOSE 8501

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# アプリケーションを実行
CMD ["python", "-m", "streamlit", "run", "/app/app/main.py", "--server.port=8501", "--server.headless=true"]