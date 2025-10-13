"""
SAIL-VL2 CLI版アプリケーション
画像とテキストから応答を生成するコマンドラインツール
"""

import sys
import argparse
from pathlib import Path
from PIL import Image

# vlmフォルダからインポート
from vlm.model_manager import ModelManager


def main():
    """CLIエントリポイント"""
    parser = argparse.ArgumentParser(
        description="SAIL-VL2 Vision Language Model CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 画像とテキストで質問
  python vlm_cli.py --image photo.jpg --prompt "この画像について説明してください"
  
  # パラメータ調整
  python vlm_cli.py --image chart.png --prompt "このグラフを分析" --temp 0.1 --top-p 0.5
  
  # テキストのみ
  python vlm_cli.py --prompt "日本の首都は？"
        """
    )
    
    # 必須引数
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        required=True,
        help="入力プロンプト（質問文）"
    )
    
    # オプション引数
    parser.add_argument(
        "--image", "-i",
        type=str,
        default=None,
        help="画像ファイルのパス"
    )
    
    parser.add_argument(
        "--model-path", "-m",
        type=str,
        default="./vlm/SAIL-VL2-2B",  # ← vlm/を追加
        help="モデルのパス（デフォルト: ./vlm/SAIL-VL2-2B）"
    )
    
    # 生成パラメータ
    parser.add_argument(
        "--temp", "--temperature",
        type=float,
        default=None,
        help="Temperature (0.0-2.0, デフォルト: 0.7)"
    )
    
    parser.add_argument(
        "--top-p", "--top_p",
        type=float,
        default=None,
        help="Top-p (0.0-1.0, デフォルト: 0.8)"
    )
    
    parser.add_argument(
        "--top-k", "--top_k",
        type=int,
        default=None,
        help="Top-k (1-100, デフォルト: 20)"
    )
    
    parser.add_argument(
        "--max-tokens", "--max_tokens",
        type=int,
        default=None,
        help="最大トークン数 (50-2048, デフォルト: 512)"
    )
    
    parser.add_argument(
        "--rep-penalty", "--repetition_penalty",
        type=float,
        default=None,
        help="Repetition Penalty (1.0-2.0, デフォルト: 1.0)"
    )
    
    parser.add_argument(
        "--preset",
        type=str,
        choices=["accurate", "balanced", "creative"],
        default=None,
        help="プリセット設定 (accurate: OCR/正確性重視, balanced: バランス型, creative: 創造的)"
    )
    
    args = parser.parse_args()
    
    # 画像読み込み
    image = None
    if args.image:
        image_path = Path(args.image)
        if not image_path.exists():
            print(f"エラー: 画像ファイルが見つかりません: {args.image}", file=sys.stderr)
            sys.exit(1)
        
        try:
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            print(f"✓ 画像を読み込みました: {image_path} ({image.size[0]}x{image.size[1]})")
        except Exception as e:
            print(f"エラー: 画像の読み込みに失敗しました: {e}", file=sys.stderr)
            sys.exit(1)
    
    # モデルマネージャー初期化
    print("\n=== SAIL-VL2モデルの初期化 ===")
    model_manager = ModelManager(model_path=args.model_path)
    
    # モデルセットアップ（進捗表示）
    def progress_callback(msg: str):
        print(f"  {msg}")
    
    success = model_manager.setup_model(progress_callback=progress_callback)
    
    if not success:
        print("\nエラー: モデルの初期化に失敗しました", file=sys.stderr)
        sys.exit(1)
    
    # デバイス情報表示
    device_info = model_manager.get_device_info()
    print(f"\n✓ 初期化完了")
    if device_info["cuda_available"]:
        print(f"  デバイス: {device_info['gpu_name']}")
        print(f"  VRAM: {device_info['gpu_memory_allocated']:.1f}GB / {device_info['gpu_memory_total']:.1f}GB")
    else:
        print(f"  デバイス: CPU")
    
    # 生成パラメータの準備
    gen_params = {}
    if args.temp is not None:
        gen_params["temperature"] = args.temp
    if args.top_p is not None:
        gen_params["top_p"] = args.top_p
    if args.top_k is not None:
        gen_params["top_k"] = args.top_k
    if args.max_tokens is not None:
        gen_params["max_new_tokens"] = args.max_tokens
    if args.rep_penalty is not None:
        gen_params["repetition_penalty"] = args.rep_penalty
    if args.preset is not None:
        gen_params["preset"] = args.preset
    
    # パラメータ表示
    print("\n=== 生成パラメータ ===")
    if args.preset:
        preset_config = model_manager.get_preset_config(args.preset)
        print(f"  プリセット: {args.preset}")
        for key, value in preset_config.items():
            print(f"    {key}: {value}")
    if gen_params:
        print("  カスタム設定:")
        for key, value in gen_params.items():
            if key != "preset":
                print(f"    {key}: {value}")
    else:
        print("  デフォルト設定を使用")
    
    # 応答生成
    print("\n=== 応答生成中... ===")
    print(f"プロンプト: {args.prompt}\n")
    
    try:
        response = model_manager.generate_response(
            text=args.prompt,
            image=image,
            **gen_params
        )
        
        # 結果表示
        print("=" * 60)
        print("応答:")
        print("=" * 60)
        print(response)
        print("=" * 60)
        
    except Exception as e:
        print(f"\nエラー: 生成中にエラーが発生しました", file=sys.stderr)
        print(f"詳細: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()