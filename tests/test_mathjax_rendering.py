"""
MathJax数式表示の完全テストコード
ResultFormatterのset_output_htmlメソッドを使って、
数式を含むMarkdownテキストをHTMLに変換し、
正しく数式が表示されるかテストする
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from tabs.formatters.result_formatter import ResultFormatter

def test_mathjax_rendering():
    """数式を含むテキストをHTMLに変換してテスト"""
    
    # 数式を含むサンプルテキスト
    sample_text = """
# 冷蔵庫のモデル作成

## 1. 理論・数式

### 1.1 熱力学的理論

冷却サイクルは4つの主要なプロセスを含みます:

1. **圧縮 (Compressor)**
   冷媒が圧縮され、高温・高圧の気体になります。
   - エネルギーバランス式:
     \\[
     W_c = m \\cdot h_{\\text{in}} - m \\cdot h_{\\text{out}}
     \\]
     ここで、\\( W_c \\) は圧縮機の仕事、\\( m \\) は質量流量、\\( h \\) は比エンタルピーです。

2. **凝縮 (Condenser)**
   高温・高圧の冷媒が熱を周囲に放出し、液体に変化します。
   - エネルギーバランス式:
     \\[
     Q_{\\text{cond}} = m \\cdot (h_{\\text{out}} - h_{\\text{in}})
     \\]

3. **膨張 (Expansion Valve)**
   冷媒が減圧され、低温・低圧の液体になります。
   - エンタルピー保存:
     \\[
     h_{\\text{in}} = h_{\\text{out}}
     \\]

4. **蒸発 (Evaporator)**
   冷媒が熱を吸収し、再び気体になります。
   - エネルギーバランス式:
     \\[
     Q_{\\text{evap}} = m \\cdot (h_{\\text{out}} - h_{\\text{in}})
     \\]

### 1.2 熱伝達

冷蔵庫内部と外部の熱伝達は、以下の熱伝達方程式で表現されます:
\\[
Q = U \\cdot A \\cdot \\Delta T
\\]
ここで、\\( U \\) は熱伝達率、\\( A \\) は伝熱面積、\\( \\Delta T \\) は温度差です。

### 1.3 エネルギー効率

冷蔵庫の性能係数 (Coefficient of Performance, COP) は、以下で定義されます:
\\[
COP = \\frac{Q_{\\text{evap}}}{W_c}
\\]

## インライン数式のテスト

インライン数式も確認: \\(E = mc^2\\) や \\(\\pi r^2\\) など。
"""
    
    # ResultFormatterを使ってHTMLに変換
    formatter = ResultFormatter()
    html_output = formatter.set_output_html(sample_text)
    
    # テスト用HTMLを保存
    test_output_path = Path("data") / "test_mathjax_output.html"
    test_output_path.write_text(html_output, encoding="utf-8")
    
    print(f"✓ テスト用HTMLを生成しました: {test_output_path}")
    print(f"✓ ファイルサイズ: {len(html_output)} bytes")
    
    # 検証: 重要な要素が含まれているか
    checks = {
        "CDN MathJax": "cdn.jsdelivr.net/npm/mathjax" in html_output,
        "MathJax Config": "window.MathJax" in html_output,
        "Display Math": "\\[" in html_output and "\\]" in html_output,
        "Inline Math": "\\(" in html_output and "\\)" in html_output,
    }
    
    print("\n【検証結果】")
    all_passed = True
    for check_name, result in checks.items():
        status = "✓ OK" if result else "✗ NG"
        print(f"  {status}: {check_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n✓ すべてのチェックに合格しました！")
        print(f"\n次のコマンドでビューアを起動して確認してください:")
        print(f"  python view_test_mathjax.py")
    else:
        print("\n✗ 一部のチェックに失敗しました。")
    
    return html_output

if __name__ == "__main__":
    test_mathjax_rendering()
