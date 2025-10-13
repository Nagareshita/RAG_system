# ui/canvas_manager.py
import dearpygui.dearpygui as dpg
import math
from agent_designer.ui.agent_settings import get_gui_metadata

class CanvasManager:
    def __init__(self, parent_designer):
        self.designer = parent_designer
        self.canvas = None
        self.dragging = False
        self.drag_offset = (0, 0)
        
    def setup_canvas(self, canvas_tag):
        """キャンバスを初期化"""
        self.canvas = canvas_tag
        self.draw_grid()
        
    def draw_grid(self):
        """グリッド背景を描画"""
        grid_size = 20
        width, height = 890, 690
        
        # 縦線
        for x in range(0, width, grid_size):
            dpg.draw_line((x, 0), (x, height), color=(40, 40, 40), parent=self.canvas)
        
        # 横線
        for y in range(0, height, grid_size):
            dpg.draw_line((0, y), (width, y), color=(40, 40, 40), parent=self.canvas)
    
    def refresh_canvas(self):
        """キャンバスを再描画"""
        dpg.delete_item(self.canvas, children_only=True)
        self.draw_grid()
        
        # 接続線を先に描画（ノードの下に表示するため）
        for i, conn in enumerate(self.designer.connections):
            try:
                from_node = next(n for n in self.designer.nodes if n['id'] == conn['from'])
                to_node = next(n for n in self.designer.nodes if n['id'] == conn['to'])
                
                # ベジェ曲線で美しい接続線を描画
                self.draw_bezier_connection(from_node, to_node, i)
                
            except StopIteration:
                pass
        
        # ノード描画
        for i, node in enumerate(self.designer.nodes):
            self.draw_node(node)
    
    def draw_node(self, node):
        """ノードを描画"""
        x, y = node['pos']
        
        # ノードタイプ別の色設定
        try:
            metadata = get_gui_metadata(node['type'])
            color_set = metadata['color']
        except (KeyError, ValueError):
            # デフォルトの色設定
            color_set = {'fill': (150, 150, 150, 200), 'border': (200, 200, 200), 'text': (255, 255, 255)}
        
        # 選択されたノードや接続開始ノードは枠を太くする
        border_thickness = 1
        border_color = color_set['border']
        
        if node == self.designer.selected_node:
            border_thickness = 4
        elif hasattr(self.designer, 'connection_start_node') and node == self.designer.connection_start_node:
            border_thickness = 4
            border_color = (255, 255, 0)  # 接続開始ノードは黄色の枠
        
        # ノード背景
        dpg.draw_rectangle([x, y], [x+100, y+50], 
                        color=border_color, 
                        fill=color_set['fill'], 
                        thickness=border_thickness,
                        parent=self.canvas)
        
        # ノードテキスト
        try:
            metadata = get_gui_metadata(node['type'])
            node_text = f"{metadata['name']}\nID:{node['id']}"
        except (KeyError, ValueError):
            node_text = f"{node['type']}\nID:{node['id']}"
        
        dpg.draw_text([x+10, y+15], node_text, 
                    color=color_set['text'], 
                    size=14, parent=self.canvas)

    def draw_bezier_connection(self, from_node, to_node, connection_index):
        """ベジエ曲線で美しい接続線を描画（簡素化版）"""
        from_x, from_y = from_node['pos']
        to_x, to_y = to_node['pos']
        
        # 接続情報から線種を取得
        connection = self.designer.connections[connection_index]
        line_type = connection.get('type', 'data_flow')
        
        # 古いconditional形式のみdata_flowに変換（conditional_flowは保持）
        if line_type == 'conditional':
            line_type = 'data_flow'
        
        # ConnectionRuleEngineから線種の色情報を取得
        line_info = self.designer.connection_engine.get_line_type_info(line_type)
        line_color = tuple(line_info.get('color', [100, 200, 255]))
        line_thickness = line_info.get('thickness', 3)
        
        # 接続点の計算（方向を考慮した改良版）
        # 右から左への接続の場合、接続元を左側に変更
        if from_x > to_x:  # 右から左への接続
            start_point = (from_x, from_y + 25)  # 左側から出る
        else:  # 左から右への接続
            start_point = (from_x + 100, from_y + 25)  # 右側から出る
        
        end_point = (to_x, to_y + 25)  # 接続先は常に左側
        
        # 制御点計算（接続方向を考慮した改良版）
        horizontal_distance = abs(end_point[0] - start_point[0])
        control_distance = max(50, min(150, horizontal_distance * 0.5))
        
        # 右から左への接続の場合、制御点の方向を調整
        if from_x > to_x:  # 右から左への接続
            control_point1 = (start_point[0] - control_distance, start_point[1])  # 左方向
            control_point2 = (end_point[0] - control_distance, end_point[1])      # 左方向
        else:  # 左から右への接続
            control_point1 = (start_point[0] + control_distance, start_point[1])  # 右方向
            control_point2 = (end_point[0] - control_distance, end_point[1])      # 左方向
        
        # ベジエ曲線描画（既存ロジック）
        try:
            dpg.draw_bezier_curve(
                start_point, 
                control_point1, 
                control_point2, 
                end_point,
                color=line_color,
                thickness=line_thickness,
                segments=50,
                parent=self.canvas
            )
        except AttributeError:
            self.draw_smooth_curve_with_lines(start_point, control_point1, control_point2, end_point, line_color, line_thickness)
        
        # 矢印描画
        self.draw_smooth_arrow_head(control_point2, end_point, line_color)
        
        # ラベル表示（簡素化）
        mid_t = 0.5
        mid_point = self.calculate_bezier_point(start_point, control_point1, control_point2, end_point, mid_t)
        
        # ラベル表示（正しい表示タイプを使用）
        display_type = line_type  # そのまま表示
        dpg.draw_text([mid_point[0]-20, mid_point[1]-25], f"{display_type}", 
                    color=(200, 200, 200), 
                    size=12, 
                    parent=self.canvas)
    
    def draw_smooth_curve_with_lines(self, p0, p1, p2, p3, line_color=(100, 200, 255), line_thickness=3):
        """線分を使ってベジェ曲線を近似描画"""
        segments = 20
        points = []
        
        for i in range(segments + 1):
            t = i / segments
            point = self.calculate_bezier_point(p0, p1, p2, p3, t)
            points.append(point)
        
        # 連続する線分で曲線を描画
        for i in range(len(points) - 1):
            dpg.draw_line(
                points[i], 
                points[i + 1],
                color=line_color,
                thickness=line_thickness,
                parent=self.canvas
            )

    def calculate_bezier_point(self, p0, p1, p2, p3, t):
        """ベジェ曲線上の点を計算（tは0-1のパラメータ）"""
        # 3次ベジェ曲線の計算式
        mt = 1 - t
        x = (mt**3 * p0[0] + 
            3 * mt**2 * t * p1[0] + 
            3 * mt * t**2 * p2[0] + 
            t**3 * p3[0])
        y = (mt**3 * p0[1] + 
            3 * mt**2 * t * p1[1] + 
            3 * mt * t**2 * p2[1] + 
            t**3 * p3[1])
        return (x, y)

    def draw_smooth_arrow_head(self, control_point, end_point, color=(80, 160, 200)):
        """ベジェ曲線の方向に合わせた矢印を描画（色指定対応）"""
        dx = end_point[0] - control_point[0]
        dy = end_point[1] - control_point[1]
        
        if dx == 0 and dy == 0:
            return
        
        angle = math.atan2(dy, dx)
        arrow_length = 12
        arrow_angle = math.pi / 5
        
        x1 = end_point[0] - arrow_length * math.cos(angle - arrow_angle)
        y1 = end_point[1] - arrow_length * math.sin(angle - arrow_angle)
        
        x2 = end_point[0] - arrow_length * math.cos(angle + arrow_angle)
        y2 = end_point[1] - arrow_length * math.sin(angle + arrow_angle)
        
        dpg.draw_line(end_point, (x1, y1), color=color, thickness=3, parent=self.canvas)
        dpg.draw_line(end_point, (x2, y2), color=color, thickness=3, parent=self.canvas)

    def get_node_at_pos(self, pos):
        """指定位置にあるノードを取得"""
        for node in self.designer.nodes:
            node_x, node_y = node['pos']
            if (node_x <= pos[0] <= node_x + 100 and 
                node_y <= pos[1] <= node_y + 50):
                return node
        return None

    def get_connection_at_pos(self, pos):
        """指定位置の近くにある接続線を検出"""
        tolerance = 15  # クリック判定の許容範囲
        
        for conn in self.designer.connections:
            try:
                from_node = next(n for n in self.designer.nodes if n['id'] == conn['from'])
                to_node = next(n for n in self.designer.nodes if n['id'] == conn['to'])
                
                # 接続線の開始点と終了点
                from_x, from_y = from_node['pos']
                to_x, to_y = to_node['pos']
                
                start_point = (from_x + 100, from_y + 25)  # 右端中央
                end_point = (to_x, to_y + 25)  # 左端中央
                
                # ベジェ曲線上の複数点をチェック
                if self._is_near_bezier_curve(pos, start_point, end_point, tolerance):
                    return conn
                    
            except StopIteration:
                continue
        
        return None

    def _is_near_bezier_curve(self, pos, start_point, end_point, tolerance):
        """ベジェ曲線の近くにあるかを判定"""
        # 制御点を計算（既存ロジックと同じ）
        horizontal_distance = abs(end_point[0] - start_point[0])
        control_distance = max(50, min(150, horizontal_distance * 0.5))
        
        control_point1 = (start_point[0] + control_distance, start_point[1])
        control_point2 = (end_point[0] - control_distance, end_point[1])
        
        # ベジェ曲線上の複数点をサンプリングして距離チェック
        for t in [i/20.0 for i in range(21)]:  # 21点でサンプリング
            bezier_point = self.calculate_bezier_point(start_point, control_point1, control_point2, end_point, t)
            distance = ((pos[0] - bezier_point[0])**2 + (pos[1] - bezier_point[1])**2)**0.5
            
            if distance <= tolerance:
                return True
        
        return False