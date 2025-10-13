import unittest
from pathlib import Path
from tabs.formatters.result_formatter import ResultFormatter

class TestMathJaxDisplay(unittest.TestCase):
    def test_debug_output_html_mathjax(self):
        # debug_output.htmlの内容を取得
        html_path = Path('data/debug_output.html')
        html = html_path.read_text(encoding='utf-8')
        # MathJaxスクリプトタグが含まれているか
        self.assertIn('MathJax-script', html)
        self.assertIn('window.MathJax', html)
        # 代表的な数式が含まれているか（例: Q = U \cdot A \cdot \Delta T）
        self.assertRegex(html, r'Q = U \\cdot A \\cdot \\Delta T')
        # display mathのタグが含まれているか（例: \[ ... \]）
        self.assertRegex(html, r'\\\[.*?\\\]')
        # inline mathのタグが含まれているか（例: \( ... \)）
        self.assertRegex(html, r'\\\(.*?\\\)')

if __name__ == '__main__':
    unittest.main()
