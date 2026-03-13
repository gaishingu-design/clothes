"""
Virtual Try-On Web App
Replicate API を使用して仮想試着画像を生成する Streamlit アプリ
"""

import io
import requests
import streamlit as st
import replicate
from PIL import Image

# ==================== 定数 ====================

# 推奨画像サイズ（Replicate モデルの最適入力サイズ）
TARGET_WIDTH = 768
TARGET_HEIGHT = 1024

# 使用する Replicate モデル
MODEL_ID = "cuuupid/idm-vton"

# 最大ファイルサイズ（バイト）
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


# ==================== 画像前処理 ====================

def resize_with_padding(image: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    アスペクト比を維持しながら画像をリサイズし、
    余白を白でパディングして target_w x target_h に合わせる。

    Args:
        image: 入力 PIL 画像
        target_w: 目標幅
        target_h: 目標高さ

    Returns:
        前処理済み PIL 画像（RGB）
    """
    image = image.convert("RGB")

    # アスペクト比を維持してリサイズ
    image.thumbnail((target_w, target_h), Image.LANCZOS)

    # 白背景のキャンバスを作成してセンタリング
    canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    offset_x = (target_w - image.width) // 2
    offset_y = (target_h - image.height) // 2
    canvas.paste(image, (offset_x, offset_y))

    return canvas


def preprocess_image(uploaded_file) -> tuple[Image.Image, io.BytesIO]:
    """
    アップロードされたファイルを読み込み、前処理して
    PIL 画像と BytesIO オブジェクトを返す。

    Args:
        uploaded_file: Streamlit の UploadedFile オブジェクト

    Returns:
        (PIL 画像, BytesIO) のタプル
    """
    # PIL で読み込み
    pil_image = Image.open(uploaded_file)

    # サイズ調整
    processed = resize_with_padding(pil_image, TARGET_WIDTH, TARGET_HEIGHT)

    # BytesIO に変換（API 送信用）
    buf = io.BytesIO()
    processed.save(buf, format="PNG")
    buf.seek(0)

    return processed, buf


def validate_file_size(uploaded_file) -> bool:
    """
    アップロードファイルのサイズが上限以内か確認する。

    Args:
        uploaded_file: Streamlit の UploadedFile オブジェクト

    Returns:
        True なら OK、False なら超過
    """
    return uploaded_file.size <= MAX_FILE_SIZE_BYTES


# ==================== Replicate API ====================

def get_replicate_client() -> replicate.Client:
    """
    Streamlit Secrets から APIトークンを取得して Replicate クライアントを初期化する。

    Returns:
        Replicate クライアントインスタンス

    Raises:
        st.error を表示して None を返す（例外はここで吸収）
    """
    try:
        token = st.secrets["REPLICATE_API_TOKEN"]
        return replicate.Client(api_token=token)
    except KeyError:
        st.error(
            "❌ REPLICATE_API_TOKEN が設定されていません。\n\n"
            "Hugging Face Spaces の Settings → Secrets、または `.streamlit/secrets.toml` に "
            "`REPLICATE_API_TOKEN` を追加してください。"
        )
        return None


def run_virtual_tryon(
    client: replicate.Client,
    person_buf: io.BytesIO,
    cloth_buf: io.BytesIO,
) -> str | None:
    """
    Replicate API を呼び出して仮想試着画像を生成する。

    Args:
        client: 初期化済み Replicate クライアント
        person_buf: 人物画像の BytesIO
        cloth_buf: 服画像の BytesIO

    Returns:
        生成画像の URL 文字列、失敗時は None
    """
    try:
        # 最新バージョンを自動取得して実行
        output = client.run(
            MODEL_ID,
            input={
                "human_img": person_buf,
                "garm_img": cloth_buf,
                "garment_des": "clothing item",  # 服の説明（任意）
                "is_checked": True,
                "is_checked_crop": False,
                "denoise_steps": 30,
                "seed": 42,
            },
        )

        # output はリストまたは文字列 URL で返ってくる
        if isinstance(output, list):
            return output[0] if output else None
        return str(output)

    except replicate.exceptions.ReplicateError as e:
        st.error(f"❌ Replicate API エラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期せぬエラーが発生しました: {e}")
        return None


# ==================== 結果表示 ====================

def fetch_image_bytes(url: str) -> bytes | None:
    """
    URL から画像バイナリを取得する。

    Args:
        url: 画像 URL

    Returns:
        画像のバイト列、失敗時は None
    """
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        return resp.content
    except requests.RequestException as e:
        st.error(f"❌ 生成画像の取得に失敗しました: {e}")
        return None


def display_result(image_url: str) -> None:
    """
    生成された試着画像を表示し、ダウンロードボタンを提供する。

    Args:
        image_url: 生成画像の URL
    """
    image_bytes = fetch_image_bytes(image_url)
    if image_bytes is None:
        return

    st.success("✅ 試着画像の生成が完了しました！")

    st.subheader("Generated Image")
    st.image(image_bytes, use_container_width=True)

    # ダウンロードボタン
    st.download_button(
        label="⬇️ Download Image",
        data=image_bytes,
        file_name="virtual_tryon_result.png",
        mime="image/png",
    )


# ==================== メイン UI ====================

def main():
    """Streamlit アプリのメインエントリーポイント"""

    # ページ設定
    st.set_page_config(
        page_title="Virtual Try-On App",
        page_icon="👗",
        layout="centered",
    )

    # タイトル
    st.title("👗 Virtual Try-On App")
    st.markdown(
        "人物写真と服の写真をアップロードすると、AIが仮想試着画像を生成します。\n\n"
        "> 推論には **10〜40秒** ほどかかります。"
    )
    st.divider()

    # ==================== 画像アップロード ====================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📷 Upload Person Image")
        st.caption("全身または上半身・正面向き推奨 / JPG・PNG / 最大10MB")
        person_file = st.file_uploader(
            "人物画像を選択",
            type=["jpg", "jpeg", "png"],
            key="person",
            label_visibility="collapsed",
        )
        if person_file:
            if not validate_file_size(person_file):
                st.error("ファイルサイズが 10MB を超えています。")
                person_file = None
            else:
                st.image(person_file, caption="Person Image", use_container_width=True)

    with col2:
        st.subheader("👔 Upload Clothing Image")
        st.caption("平置きまたはトルソー画像 / JPG・PNG / 最大10MB")
        cloth_file = st.file_uploader(
            "服画像を選択",
            type=["jpg", "jpeg", "png"],
            key="clothing",
            label_visibility="collapsed",
        )
        if cloth_file:
            if not validate_file_size(cloth_file):
                st.error("ファイルサイズが 10MB を超えています。")
                cloth_file = None
            else:
                st.image(cloth_file, caption="Clothing Image", use_container_width=True)

    st.divider()

    # ==================== 生成ボタン ====================
    generate_disabled = person_file is None or cloth_file is None
    generate_clicked = st.button(
        "✨ Generate Try-On",
        type="primary",
        disabled=generate_disabled,
        use_container_width=True,
    )

    if generate_disabled and not generate_clicked:
        st.info("👆 人物画像と服画像の両方をアップロードしてください。")

    # ==================== 推論実行 ====================
    if generate_clicked and person_file and cloth_file:

        # Replicate クライアント初期化
        client = get_replicate_client()
        if client is None:
            st.stop()

        # 画像前処理
        with st.spinner("🔄 画像を前処理中..."):
            _, person_buf = preprocess_image(person_file)
            _, cloth_buf = preprocess_image(cloth_file)

        # API 呼び出し
        with st.spinner("🤖 Generating virtual try-on image...（10〜40秒かかります）"):
            result_url = run_virtual_tryon(client, person_buf, cloth_buf)

        # 結果表示
        if result_url:
            st.divider()
            display_result(result_url)


# ==================== エントリーポイント ====================

if __name__ == "__main__":
    main()
