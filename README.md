# 👗 Virtual Try-On App

Replicate API（`cuuupid/idm-vton`）を使って、人物写真に任意の服を着せた画像を AI が生成する Streamlit アプリです。

---

## 🖥️ アプリ概要

| 項目 | 内容 |
|------|------|
| フレームワーク | Streamlit |
| AI モデル | `cuuupid/idm-vton`（Replicate） |
| 推論時間の目安 | 10〜40 秒 |
| 対応画像形式 | JPG / PNG（最大 10MB） |
| デプロイ先 | Hugging Face Spaces |

### 処理フロー

```
ユーザー画像アップロード
        ↓
画像前処理（768×1024 にリサイズ＋パディング）
        ↓
Replicate API へ送信
        ↓
AI 推論（GPU サーバー）
        ↓
生成画像 URL 取得
        ↓
画面表示 ＋ ダウンロード
```

---

## ⚙️ セットアップ方法

### 1. リポジトリのクローン

```bash
git clone https://huggingface.co/spaces/<your-username>/<your-space-name>
cd <your-space-name>
```

### 2. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 3. API キーの設定

#### ローカル開発の場合

`.streamlit/secrets.toml` を作成して以下を記述します。

```toml
REPLICATE_API_TOKEN = "r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

> ⚠️ `.streamlit/secrets.toml` は `.gitignore` に追加してリポジトリに含めないでください。

#### Hugging Face Spaces の場合

Spaces の **Settings → Variables and secrets** から Secret を追加します。

| キー | 値 |
|------|----|
| `REPLICATE_API_TOKEN` | Replicate の API トークン |

Replicate のトークンは [https://replicate.com/account/api-tokens](https://replicate.com/account/api-tokens) から取得できます。

### 4. アプリの起動（ローカル）

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` を開くとアプリが表示されます。

---

## 🚀 Hugging Face Spaces へのデプロイ

1. Hugging Face で新しい Space を作成（SDK: **Streamlit** を選択）
2. 以下のファイルをアップロードまたは push します。
   - `app.py`
   - `requirements.txt`
   - `README.md`
3. Settings → Secrets に `REPLICATE_API_TOKEN` を登録します。
4. Space が自動ビルドされ、数分後に公開されます。

---

## 📋 使い方

```
Virtual Try-On App

Upload Person Image        Upload Clothing Image
[人物の写真を選択]          [服の写真を選択]

         [✨ Generate Try-On]

              Processing...

           Generated Image
            [⬇️ Download Image]
```

1. **人物画像をアップロード** — 全身または上半身・正面向き推奨
2. **服画像をアップロード** — 平置きまたはトルソー画像推奨
3. **Generate Try-On ボタンをクリック** — AI が試着画像を生成（10〜40 秒）
4. 生成された画像を **ダウンロード**

---

## 📁 ファイル構成

```
.
├── app.py              # Streamlit アプリ本体
├── requirements.txt    # 依存ライブラリ
└── README.md           # このファイル
```

---

## 🛠️ 使用技術

- [Streamlit](https://streamlit.io/) — UI フレームワーク
- [Replicate](https://replicate.com/) — AI 推論 API
- [cuuupid/idm-vton](https://replicate.com/cuuupid/idm-vton) — 仮想試着 AI モデル
- [Pillow](https://pillow.readthedocs.io/) — 画像処理
- [rembg](https://github.com/danielgatis/rembg) — 背景削除（オプション）

---

## ⚠️ 注意事項

- Replicate API の利用には課金が発生します（従量制）。
- 生成画像は Replicate のサーバーに一時保存されます。利用規約をご確認ください。
- 著作権のある画像の使用は避けてください。
