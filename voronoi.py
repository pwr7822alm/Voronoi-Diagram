# $LAN=PYTHON$
# Englihs Name: Hsin-Yi, You            
# Chinese Name：尤心怡                  
# Student ID: M133140001                
import sys
import math
import numpy as np
# 看答案用
from scipy.spatial import Voronoi
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QMessageBox,
    QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, QGraphicsLineItem,
    QHBoxLayout, QVBoxLayout, QWidget, QTextEdit, QFrame
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen

class Edge:
    def __init__(self, start_point, end_point, left_point=None, right_point=None):
        self.start_point = start_point
        self.end_point = end_point
        self.left_point = left_point  
        self.right_point = right_point  

class VoronoiDiagram:
    def __init__(self, points, edges):
        self.points = points  
        self.edges = edges  

class VoronoiView(QGraphicsView):
    def __init__(self, scene, coordinates_display):
        super().__init__(scene)
        self.setSceneRect(QRectF(0, 0, 600, 600))
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(1)
        self.setFixedSize(600, 600)  
        self.points = []
        self.edges = []
        self.coordinates_display = coordinates_display

    def mousePressEvent(self, event):
        ''' 滑鼠點擊事件 '''
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            x, y = pos.x(), pos.y()
            if 0 <= x <= 600 and 0 <= y <= 600:  
                self.drawPoint((x, y))
                self.points.append((x, y))
                self.updateCoordinatesDisplay()

    def updateCoordinatesDisplay(self):
        ''' 更新座標顯示 '''
        text = "點座標列表：\n"
        for i, point in enumerate(self.points, 1):
            text += f"點 {i}: ({int(point[0])}, {int(point[1])})\n"
        self.coordinates_display.setText(text)

    def drawPoint(self, point, color=Qt.black):
        ''' 繪製點 '''
        x, y = point
        ellipse = QGraphicsEllipseItem(x - 2, y - 2, 4, 4)
        ellipse.setBrush(color)
        self.scene().addItem(ellipse)
        return ellipse  # 返回繪製的圖形

    def drawLine(self, start_point, end_point, color=Qt.blue, line_style=Qt.SolidLine):
        ''' 繪製線段 '''
        line = QGraphicsLineItem(start_point[0], start_point[1],end_point[0], end_point[1])
        pen = QPen(color)
        pen.setStyle(line_style)
        pen.setWidth(1)
        line.setPen(pen)
        self.scene().addItem(line)
        return line  # 返回繪製的線段

def clipLineToRect(line, rect):
    """ 將線段裁剪到矩形範圍內，使用 Cohen-Sutherland 演算法 """
    x_min, y_min, x_max, y_max = rect
    x1, y1 = line[0]
    x2, y2 = line[1]

    # 定義位元碼
    INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8

    def compute_out_code(x, y):
        code = INSIDE
        if x < x_min:
            code |= LEFT
        elif x > x_max:
            code |= RIGHT
        if y < y_min:
            code |= BOTTOM
        elif y > y_max:
            code |= TOP
        return code

    out_code1 = compute_out_code(x1, y1)
    out_code2 = compute_out_code(x2, y2)

    accept = False

    while True:
        if not (out_code1 | out_code2):
            # 兩點都在矩形內
            accept = True
            break
        elif out_code1 & out_code2:
            # 兩點在矩形外且同側，線段不可見
            break
        else:
            # 線段部分在矩形內
            x, y = 0, 0
            # 選擇在矩形外的點
            out_code_out = out_code1 if out_code1 else out_code2
            if out_code_out & TOP:
                x = x1 + (x2 - x1) * (y_max - y1) / (y2 - y1)
                y = y_max
            elif out_code_out & BOTTOM:
                x = x1 + (x2 - x1) * (y_min - y1) / (y2 - y1)
                y = y_min
            elif out_code_out & RIGHT:
                y = y1 + (y2 - y1) * (x_max - x1) / (x2 - x1)
                x = x_max
            elif out_code_out & LEFT:
                y = y1 + (y2 - y1) * (x_min - x1) / (x2 - x1)
                x = x_min

            if out_code_out == out_code1:
                x1, y1 = x, y
                out_code1 = compute_out_code(x1, y1)
            else:
                x2, y2 = x, y
                out_code2 = compute_out_code(x2, y2)

    if accept:
        return (x1, y1), (x2, y2)
    else:
        return None  # 線段不在矩形內

class VoronoiApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.point_sets = []  # 用於存儲多組點資料
        self.current_set_index = -1  # 當前顯示的點集合索引
        self.edges = []  # 用於存儲 Voronoi 圖的邊
        self.is_step_by_step = False  # 是否處於 step by step 模式
        self.step = 0  # 當前的步驟
        self.auxiliary_lines = []  # 用於存儲輔助線
        self.auxiliary_points = []  # 用於存儲輔助點
        self.VoronoiDiagram = VoronoiDiagram([], [])  # 用於存儲 Voronoi 圖
        self.sweep_line_y = 0  # 掃描線的當前 y 座標
        # 初始化視窗
        self.initUI()

    def initUI(self):
        """初始化使用者介面"""
        # 設定主視窗
        self.setWindowTitle('Voronoi Diagram')
        self.setGeometry(100, 100, 850, 1000)

        # 創建主要的widget和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # 初始化三個主要區域
        self.initCanvasArea()
        self.initButtonArea()
        
        # 將區域添加到主布局
        self.main_layout.addWidget(self.canvas_widget)
        self.main_layout.addWidget(self.button_widget)

    def initCanvasArea(self):
        """初始化畫布區域(區域1)和座標顯示區域(區域3)"""
        # 創建畫布容器
        self.canvas_widget = QWidget()
        self.canvas_layout = QVBoxLayout(self.canvas_widget)
        
        # 初始化場景
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(QRectF(0, 0, 600, 600))
        
        # 創建座標顯示區域
        self.coordinates_display = QTextEdit()
        self.coordinates_display.setReadOnly(True)
        self.coordinates_display.setFixedHeight(150)
        
        # 初始化視圖
        self.view = VoronoiView(self.scene, self.coordinates_display)
        
        # 添加到畫布布局
        self.canvas_layout.addWidget(self.view)
        self.canvas_layout.addWidget(self.coordinates_display)

    def initButtonArea(self):
        """初始化按鈕區域(區域2)"""
        # 創建按鈕容器
        self.button_widget = QWidget()
        self.button_layout = QVBoxLayout(self.button_widget)
        self.button_layout.setAlignment(Qt.AlignTop)

        # 定義按鈕
        buttons = [
            ('清空', self.clearScene),
            ('Run', self.drawVoronoi),
            ('Step by Step', self.startStepByStep),
            ('讀取檔案', self.loadInputFile),
            ('儲存檔案', self.saveOutputFile),
            ('載入結果', self.loadResultFile),
            ('上一組點', self.showPreviousSet),
            ('下一組點', self.showNextSet),
            ('看答案(4點UP)', self.showAnswer)
        ]

        # 創建並設置按鈕
        for button_text, callback in buttons:
            button = QPushButton(button_text)
            button.setFixedSize(120, 30)
            button.clicked.connect(callback)
            self.button_layout.addWidget(button)
            self.button_layout.addSpacing(5)

        # 添加彈性空間
        self.button_layout.addStretch()

    def clearScene(self):
        self.view.scene().clear()
        self.view.points.clear()
        self.edges.clear()
        self.coordinates_display.clear()
    
    def showCurrentSet(self):
        """ 顯示當前選擇的點集合 """
        if 0 <= self.current_set_index < len(self.point_sets):
            self.clearScene()
            self.view.points = self.point_sets[self.current_set_index][:]
            for point in self.view.points:
                self.view.drawPoint(point)
            self.view.updateCoordinatesDisplay()
        else:
            QMessageBox.information(self, '提示', '沒有可顯示的點集合。')

    def showNextSet(self):
        """ 顯示下一組點集合 """
        if self.point_sets:
            self.current_set_index = (self.current_set_index + 1) % len(self.point_sets)
            self.showCurrentSet()
        else:
            QMessageBox.information(self, '提示', '沒有可顯示的點集合。')

    def showPreviousSet(self):
        "" "顯示上一組點集合 """
        if self.point_sets:
            self.current_set_index = (self.current_set_index - 1) % len(self.point_sets)
            self.showCurrentSet()
        else:
            QMessageBox.information(self, '提示', '沒有可顯示的點集合。')

    def drawVoronoiDiagram(self, voronoi_diagram, color=Qt.blue):
        """ 根據點的數量，繪製 Voronoi 圖 (divideConquer) """
        for edge in voronoi_diagram.edges:
            self.view.drawLine(edge.start_point, edge.end_point, color=color)
            self.edges.append((edge.start_point, edge.end_point))

    def drawVoronoi(self):
        """ 根據點的數量，繪製 Voronoi 圖 """
        # 清除畫布和相關資料
        self.view.scene().clear()
        self.edges.clear()
        self.view.updateCoordinatesDisplay()
        for point in self.view.points:
            self.view.drawPoint(point)

        if self.is_step_by_step:
            # 如果在Step by Step模式中，直接繪製最終結果，並移除輔助線
            self.is_step_by_step = False
        # 排序點
        point = sorted(self.removeOverlappingPoints(self.view.points), key=lambda p: (p[0], p[1]))
        num_points = len(point)
        if num_points == 0:
            QMessageBox.information(self, '提示', '請先添加點。')
            return
        elif num_points == 1:
            QMessageBox.information(self, '提示', '單個點的 Voronoi 圖為整個平面。')
            return
        elif num_points == 2:
            self.drawVoronoiDiagram(self.computeVoronoiForTwoPoints(point))
        elif self.colinear(point):
            self.drawVoronoiDiagram(self.computeVoronoiForCollinear(point))
        elif num_points == 3:
            self.drawVoronoiDiagram(self.computeVoronoiForThreePoints(point))
        else:
            vor, hp = self.divideAndConquer(point)
            self.drawVoronoiDiagram(vor)
            for h in hp:
                self.view.drawLine(h[0], h[1], color=Qt.red, line_style=Qt.DashLine)
            self.drawConvexHull(self.computeConvexHull(point), color=Qt.black, line_style=Qt.DashLine)

    def removeOverlappingPoints(self, points_list):
        """ 移除重疊的點 """
        if not points_list:
            return []
        
        # 先將所有點轉換為整數座標，並建立與原始點的對應
        point_map = {}  # 用來儲存整數座標到原始點的映射
        for point in points_list:
            int_pos = (point[0], point[1])
            if int_pos not in point_map:
                point_map[int_pos] = []
            point_map[int_pos].append(point)
        
        # 對於每個整數座標，只保留一個對應的原始點
        unique_points = [points[0] for points in point_map.values()]
        
        return unique_points

    def startStepByStep(self):
        """開始或繼續Step by Step模式"""
        if not self.is_step_by_step:
            temp_points = self.view.points
            self.view.scene().clear()
            for point in temp_points:
                self.view.drawPoint(point)
            self.view.updateCoordinatesDisplay()
            self.is_step_by_step = True
            self.step = 1
            self.auxiliary_lines = []
            self.auxiliary_points = []
            # 不顯示提示訊息，直接執行第一步
        # 繼續執行下一步
        point = sorted(self.removeOverlappingPoints(self.view.points), key=lambda p: (p[0], p[1]))
        num_points = len(point)
        if num_points == 2:
            self.stepByStepTwoPoints(point)
        elif num_points == 3:
            self.stepByStepThreePoints(point)
        else:
            self.stepByStepMultiplePoints(point)

    def stepByStepTwoPoints(self, points):
        # 兩點重合的情況
        p1, p2 = points
        if p1 == p2:
            QMessageBox.warning(self, '錯誤', '兩點重合，無法計算垂直平分線。')
            self.is_step_by_step = False
            self.removeAuxiliaryItems()
            return
        if self.step == 1:
            # 繪製連接兩點的線段
            line = self.view.drawLine(p1, p2, color=Qt.green)
            self.auxiliary_lines.append(line)
            self.step += 1
        elif self.step == 2:
            # 繪製兩點的中點
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2
            point = self.view.drawPoint((mid_x, mid_y))
            self.auxiliary_points.append(point)
            self.step += 1
        elif self.step == 3:
            # 繪製垂直平分線
            start, end = self.computePerpendicularBisector(p1, p2)
            line = self.view.drawLine(start, end)
            self.edges.append((start, end))
            self.step += 1
            QMessageBox.information(self, '提示', 'Step by Step完成。')
            self.is_step_by_step = False
            self.removeAuxiliaryItems()  # 移除輔助線和輔助點
        else:
            QMessageBox.information(self, '提示', 'Step by Step完成。')
            self.is_step_by_step = False

    def stepByStepThreePoints(self, points):
        p1, p2, p3 = points
        # 三點重合的情況
        if p1 == p2 == p3:
            QMessageBox.warning(self, '錯誤', '三點重合，無法計算 Voronoi 圖。')
            self.is_step_by_step = False
            self.removeAuxiliaryItems()
            return
        if self.step == 1:
            # 繪製三角形
            line1 = self.view.drawLine(p1, p2, color=Qt.green)
            line2 = self.view.drawLine(p2, p3, color=Qt.green)
            line3 = self.view.drawLine(p3, p1, color=Qt.green)
            self.auxiliary_lines.extend([line1, line2, line3])
            self.step += 1
        elif self.step == 2:
            # 計算並繪製外心
            center = self.circumcenter(p1, p2, p3)
            if center:
                point = self.view.drawPoint(center)
                self.auxiliary_points.append(point)
                self.step += 1
            else:
                edges = self.handleColinearCase(p1, p2, p3)
                for edge in edges:
                    self.view.drawLine(edge.start_point, edge.end_point)
                    self.edges.append((edge.start_point, edge.end_point))
                QMessageBox.information(self, '提示', 'Step by Step 完成。')
                self.is_step_by_step = False
                self.removeAuxiliaryItems()
        elif self.step == 3:
            # 繪製 Voronoi 邊
            edges = self.handleNonColinearCase(p1, p2, p3)
            for edge in edges:
                self.view.drawLine(edge.start_point, edge.end_point)
                self.edges.append((edge.start_point, edge.end_point))
            self.step += 1
            QMessageBox.information(self, '提示', 'Step by Step 完成。')
            self.is_step_by_step = False
            self.removeAuxiliaryItems()
        else:
            QMessageBox.information(self, '提示', 'Step by Step 完成。')
            self.is_step_by_step = False

    def stepByStepMultiplePoints(self, points):
        num_points = len(points)
        #  lexical order
        points = sorted(points, key=lambda p: (p[0], p[1]))
        # 如果是奇數，左邊多一個點
        mid = num_points // 2
        if num_points % 2 == 1:
            mid += 1
        left_points = points[:mid]
        right_points = points[mid:]
        vor, hp = self.divideAndConquer(points)
        if self.step == 1:
            # 畫左邊的點
            for point in left_points:
                self.view.drawPoint(point, color=Qt.red)
            self.drawVoronoiDiagram(self.divideAndConquer(left_points), color=Qt.magenta)
            self.step += 1
        elif self.step == 2:
            # 畫右邊的點
            for point in right_points:
                self.view.drawPoint(point, color=Qt.green)
            self.drawVoronoiDiagram(self.divideAndConquer(right_points), color=Qt.green)
            self.step += 1
        elif self.step == 3:
            # 畫左凸包
            hull_left = self.computeConvexHull(left_points)
            self.drawConvexHull(hull_left, color=Qt.magenta, line_style=Qt.DashLine)
            self.step += 1
        elif self.step == 4:
            # 畫右凸包
            hull_right = self.computeConvexHull(right_points)
            self.drawConvexHull(hull_right, color=Qt.green, line_style=Qt.DashLine)
            self.step += 1
        elif self.step == 5:
            # 畫 hyperplane
            for p in hp:
                self.view.drawLine(p[0], p[1], color=Qt.red)
            self.step += 1
        elif self.step == 6:
            # 畫合併後的凸包，和 voronoi
            self.view.scene().clear()
            for point in points:
                self.view.drawPoint(point)
            merged_hull = self.computeConvexHull(points)
            self.drawConvexHull(merged_hull, color=Qt.black, line_style=Qt.DashLine)
            self.drawVoronoiDiagram(vor, color=Qt.blue)
            QMessageBox.information(self, '提示', 'Step by Step 完成。')
            self.is_step_by_step = False

    def computeVoronoiForCollinear(self, points):
        edges = []
        # 確定共線方向
        (x0, y0), (x1, y1) = points[0], points[1]
        dx = x1 - x0
        dy = y1 - y0
        
        # 計算共線直線的方向向量
        if dx != 0:
            slope = dy / dx
        else:
            slope = float('inf')  # 垂直線
        
        # 計算垂直於共線直線的方向向量
        if slope == float('inf'):
            perp_slope = 0  # 水平線
        elif slope == 0:
            perp_slope = float('inf')  # 垂直線
        else:
            perp_slope = -1 / slope  # 垂直於共線直線
        
        # 定義延伸的距離（模擬無限）
        EXTEND_DISTANCE = 10000
        
        # 生成垂直平分線
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2
            
            if perp_slope == float('inf'):
                # 垂直平分線為垂直線
                start_point = (mid_x, mid_y - EXTEND_DISTANCE)
                end_point = (mid_x, mid_y + EXTEND_DISTANCE)
            elif perp_slope == 0:
                # 垂直平分線為水平線
                start_point = (mid_x - EXTEND_DISTANCE, mid_y)
                end_point = (mid_x + EXTEND_DISTANCE, mid_y)
            else:
                # 一般情況，計算兩個點以形成直線
                # 使用方向向量延伸線段
                dx_perp = 1
                dy_perp = perp_slope
                # 正規化方向向量
                norm = math.hypot(dx_perp, dy_perp)
                dx_perp /= norm
                dy_perp /= norm
                # 延伸線段
                start_point = (mid_x - dx_perp * EXTEND_DISTANCE, mid_y - dy_perp * EXTEND_DISTANCE)
                end_point = (mid_x + dx_perp * EXTEND_DISTANCE, mid_y + dy_perp * EXTEND_DISTANCE)
            
            edge = Edge(start_point, end_point, left_point=p1, right_point=p2)
            edges.append(edge)
        
        return VoronoiDiagram(points, edges)

    def removeAuxiliaryItems(self):
        """移除輔助線和輔助點"""
        for item in self.auxiliary_lines:
            self.view.scene().removeItem(item)
        self.auxiliary_lines.clear()
        for item in self.auxiliary_points:
            self.view.scene().removeItem(item)
        self.auxiliary_points.clear()

    def computePerpendicularBisector(self, p1, p2):
        """ 計算兩點之間的垂直平分線 """
        mid_x = (p1[0] + p2[0]) / 2
        mid_y = (p1[1] + p2[1]) / 2
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        if dx == 0:
            # 垂直線，垂直平分線為水平線
            start_point = (0, mid_y)
            end_point = (1000, mid_y)
        elif dy == 0:
            # 水平線，垂直平分線為垂直線
            start_point = (mid_x, 0)
            end_point = (mid_x, 1000)
        else:
            slope = -dx / dy
            intercept = mid_y - slope * mid_x
            # 計算與畫布邊界的交點
            x1 = 0
            y1 = slope * x1 + intercept
            x2 = 1000
            y2 = slope * x2 + intercept
            start_point = (x1, y1)
            end_point = (x2, y2)
        return start_point, end_point
    
    def circumcenter(self, a, b, c):
            """ 計算三角形的外心 """
            d = 2 * (a[0]*(b[1]-c[1]) + b[0]*(c[1]-a[1]) + c[0]*(a[1]-b[1]))
            if d == 0:
                return None
            ux = ((a[0]**2 + a[1]**2)*(b[1]-c[1]) + (b[0]**2 + b[1]**2)*(c[1]-a[1]) + (c[0]**2 + c[1]**2)*(a[1]-b[1])) / d
            uy = ((a[0]**2 + a[1]**2)*(c[0]-b[0]) + (b[0]**2 + b[1]**2)*(a[0]-c[0]) + (c[0]**2 + c[1]**2)*(b[0]-a[0])) / d
            return (ux, uy)

    def computeVoronoiForTwoPoints(self, points):
        p1, p2 = points
        edges = []
        if p1 == p2:
            QMessageBox.warning(self, '錯誤', '兩點重合，無法計算垂直平分線。')
            return VoronoiDiagram(points, edges)
        
        start, end = self.computePerpendicularBisector(p1, p2)
        edge = Edge(start, end, left_point=p1, right_point=p2)
        edges.append(edge)
        return VoronoiDiagram(points, edges)

    def computeVoronoiForThreePoints(self, points):
        """ 計算三個點的 Voronoi 圖 """
        p1, p2, p3 = points
        edges = []

        # 檢測三點是否共線
        if self.colinear(points):
            # 三點共線的處理
            edges.extend(self.handleColinearCase(p1, p2, p3))
        else:
            # 三點不共線，正常處理
            edges.extend(self.handleNonColinearCase(p1, p2, p3))
        return VoronoiDiagram(points, edges)

    def colinear(self, points, epsilon=1e-9):
        """ 判斷多個點是否共線 """
        if len(points) < 3:
            return True
        A, B, C = self.calculateLineABC(points[0], points[1])
        for (x, y) in points:
            value = A * x + B * y + C
            if abs(value) > 0:
                return False
        return True

    def handleColinearCase(self, p1, p2, p3):
        """ 處理三點共線的情況 """
        edges = []
        # 將點按照 x 座標排序（如果 x 相同，則按照 y 座標）
        points = sorted([p1, p2, p3], key=lambda p: (p[0], p[1]))
        # 計算相鄰點的垂直平分線
        for i in range(2):
            mid_x = (points[i][0] + points[i+1][0]) / 2
            mid_y = (points[i][1] + points[i+1][1]) / 2
            dx = points[i+1][0] - points[i][0]
            dy = points[i+1][1] - points[i][1]
            # 垂直向量
            perp_dx = -dy
            perp_dy = dx
            # 避免零向量
            if perp_dx == 0 and perp_dy == 0:
                continue
            # 延伸線段
            length = 10000
            norm = math.hypot(perp_dx, perp_dy)
            unit_dx = perp_dx / norm
            unit_dy = perp_dy / norm
            start_point = (mid_x - unit_dx * length, mid_y - unit_dy * length)
            end_point = (mid_x + unit_dx * length, mid_y + unit_dy * length)
            edge = Edge(start_point, end_point, left_point=points[i], right_point=points[i+1])
            edges.append(edge)
        return edges

    def handleNonColinearCase(self, p1, p2, p3, draw=True):
        ''' 處理三點不共線的問題 '''
        edges = []
        # 計算外心
        center = self.circumcenter(p1, p2, p3)
        if center is None:
            return edges

        # 將點轉換為 numpy 陣列
        center = np.array(center)
        points = [np.array(p) for p in [p1, p2, p3]]

         # 對於每條邊
        for i in range(3):
            a = points[i]
            b = points[(i + 1) % 3]
            c = points[(i + 2) % 3]

            # 計算邊的中點
            mid = (a + b) / 2
            # 計算邊的方向向量
            v = b - a
            # 計算垂直於邊的向量
            perp_v = np.array([-v[1], v[0]])
            # 正規化垂直向量
            norm = np.linalg.norm(perp_v)
            if norm == 0:
                continue
            perp_unit = perp_v / norm

            # 計算第三個點相對於垂直平分線的位置
            d_c = np.dot((c - mid), perp_unit)

            # 延伸方向為遠離第三個點的方向
            if d_c > 0:
                direction = -perp_unit
            else:
                direction = perp_unit

            # 延伸線段
            length = 10000
            start_point = center
            end_point = mid + direction * length
            edge = Edge(tuple(start_point), tuple(end_point), left_point=tuple(a), right_point=tuple(b))
            edges.append(edge)
        return edges

    def divideAndConquer(self, points):
        """ 使用分治法找 Voronoi Diagram """
        num_points = len(points)
        if num_points == 1:
            return VoronoiDiagram(points, [])
        elif num_points == 2:
            return self.computeVoronoiForTwoPoints(points)
        elif num_points == 3:
            return self.computeVoronoiForThreePoints(points)
        else:
            # Divide : 如果是奇數點，左邊多一個點
            mid = num_points // 2
            if num_points % 2 == 1:
                mid += 1
            left_points = points[:mid]
            right_points = points[mid:]
            # Recursive
            vd_left = self.divideAndConquer(left_points)
            vd_right = self.divideAndConquer(right_points)
            # merge
            merged_voronoi = self.mergeVoronoiDiagrams(vd_left, vd_right)
            return merged_voronoi

    def drawConvexHull(self, hull_points, color=Qt.red, line_style=Qt.SolidLine):
        """畫 convex hull"""
        num_points = len(hull_points)
        for i in range(num_points):
            start_point = hull_points[i]
            end_point = hull_points[(i + 1) % num_points]
            line = self.view.drawLine(start_point, end_point, color=color, line_style=line_style)
            self.auxiliary_lines.append(line)

    def computeConvexHull(self, points):
        """ 找 convex hull """
        if len(points) < 3:
            return points
        else:
            upper = []
            for p in points:
                while len(upper) >= 2 and self.cross(upper[-2], upper[-1], p) <= 0:
                    upper.pop()
                upper.append(p)
            lower = []
            for p in reversed(points):
                while len(lower) >= 2 and self.cross(lower[-2], lower[-1], p) <= 0:
                    lower.pop()
                lower.append(p)
            convex_hull = upper[:-1] + lower[:-1]
            return convex_hull

    def cross(self, o, a, b):
        """ 計算 oa 和 ob 的叉積 """
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def findUpperLowerTangents(self, hull_left, hull_right):
        """找上、下公切線，列舉所有候選切線並篩選最正確的"""
        i = self.getRightmostPointIndex(hull_left)
        j = self.getLeftmostPointIndex(hull_right)

        # 儲存候選切線
        upper_candidates = []
        lower_candidates = []

        # 找所有候選上切線
        initial_i, initial_j = i, j
        while True:
            changed = False
            while self.cross(hull_right[j], hull_left[i], hull_left[(i - 1) % len(hull_left)]) > 0:
                i = (i - 1) % len(hull_left)
                changed = True
            while self.cross(hull_left[i], hull_right[j], hull_right[(j + 1) % len(hull_right)]) < 0:
                j = (j + 1) % len(hull_right)
                changed = True
            if not changed:
                # 記錄候選切線
                upper_candidates.append((hull_left[i], hull_right[j]))
                break

        # 重置 i, j
        i, j = initial_i, initial_j

        # 找所有候選下切線
        while True:
            changed = False
            while self.cross(hull_right[j], hull_left[i], hull_left[(i + 1) % len(hull_left)]) < 0:
                i = (i + 1) % len(hull_left)
                changed = True
            while self.cross(hull_left[i], hull_right[j], hull_right[(j - 1) % len(hull_right)]) > 0:
                j = (j - 1) % len(hull_right)
                changed = True
            if not changed:
                # 記錄候選切線
                lower_candidates.append((hull_left[i], hull_right[j]))
                break

        # 根據條件篩選最正確的上切線和下切線
        def is_valid_tangent(tangent):
            """判斷切線是否有效（不穿過凸包）"""
            left, right = tangent
            for point in hull_left:
                if self.cross(right, left, point) < 0:  # 點位於切線右側
                    return False
            for point in hull_right:
                if self.cross(left, right, point) < 0:  # 點位於切線右側
                    return False
            return True

        # 篩選最終的上切線和下切線
        valid_upper_tangents = [t for t in upper_candidates if is_valid_tangent(t)]
        valid_lower_tangents = [t for t in lower_candidates if is_valid_tangent(t)]

        # 返回第一個有效切線作為最終結果（若有多條，這裡可以調整邏輯選擇最優解）
        upper_tangent = valid_upper_tangents[0] if valid_upper_tangents else upper_candidates[0]
        lower_tangent = valid_lower_tangents[0] if valid_lower_tangents else lower_candidates[0]

        return upper_tangent, lower_tangent

    def getRightmostPointIndex(self, hull):
        """ convex hull 最右點的索引 """
        max_x = max(hull, key=lambda p: p[0])[0]
        for idx, p in enumerate(hull):
            if p[0] == max_x:
                return idx
        return 0

    def getLeftmostPointIndex(self, hull):
        """ convex hull 最左點的索引 """
        min_x = min(hull, key=lambda p: p[0])[0]
        for idx, p in enumerate(hull):
            if p[0] == min_x:
                return idx
        return 0

    def mergeVoronoiDiagrams(self, vd_left, vd_right):
        """合併左右兩個 Voronoi 圖"""
        points_left = vd_left.points
        points_right = vd_right.points
        
        # 初始化記錄變數
        recorded_edges = []        # 存碰到的邊，按順序
        intersection_points = []   # 存交點，順序對應 recorded_edges
        bisector_lines = []       # 存原始中垂線，順序對應 recorded_edges
        hyperplane = []           # 存處理過的 hyperplane
        used_points = set()       # 存掃描線走過的端點
        
        # 1. 找到上下切線
        hull_left = self.computeConvexHull(points_left)
        hull_right = self.computeConvexHull(points_right)
        upper_tangent, lower_tangent = self.findUpperLowerTangents(hull_left, hull_right)
        
        # 初始化掃描線為上切線
        scan = upper_tangent
        last_intersection = (0, 0)
        used_edges = set()  # 添加已使用邊的集合

        while True:
            # 2. 找中垂線
            perp_start, perp_end = self.computePerpendicularBisector(scan[0], scan[1])
            if perp_start[1] > perp_end[1]:
                perp_start, perp_end = perp_end, perp_start
                
            # 存當前的中垂線
            bisector_lines.append([perp_start, perp_end])
            
            # 3. 找所有交點，選 y 最小的，和對應的 voronoi edge
            min_y = float('inf')
            current_intersection = None
            current_edge = None
            
            for edge in vd_left.edges + vd_right.edges:
                if id(edge) in used_edges:
                    continue
                intersection = self.computeLineIntersection((perp_start, perp_end), edge)
                if intersection:
                    if intersection[1] < min_y:
                    # if intersection[1] < min_y and intersection[1] > last_intersection[1]:
                    # if intersection[1] < min_y and intersection not in intersection_points and intersection[1] > last_intersection[1]:
                        min_y = intersection[1]
                        current_intersection = intersection
                        current_edge = edge
            
            # 記錄碰到的邊和對應的交點
            if current_intersection:
                # 記錄使用過的邊
                used_edges.add(id(current_edge))
                recorded_edges.append(current_edge)
                intersection_points.append(current_intersection)
                
                # 處理 hyperplane
                if not hyperplane:
                    # 第一條：從中垂線下端點到交點
                    if perp_start[1] > perp_end[1]:
                        perp_start, perp_end = perp_end, perp_start
                    hyperplane.append((perp_start, current_intersection))
                elif scan == lower_tangent or scan == (lower_tangent[1], lower_tangent[0]):
                    # 最後一條：從上一個交點到中垂線上端點
                    if perp_start[1] > perp_end[1]:
                        perp_start, perp_end = perp_end, perp_start
                    hyperplane.append((last_intersection, perp_end))
                    break
                else:
                    # 中間的線：從上一個交點到當前交點
                    hyperplane.append((last_intersection, current_intersection))
                
                last_intersection = current_intersection
                    
                
                if current_edge in vd_left.edges:
                         # 左邊的邊，更新左端點
                    next_point = None
                    if current_edge.left_point not in scan:
                            next_point = current_edge.left_point
                    elif current_edge.right_point not in scan:
                            next_point = current_edge.right_point
                    scan = (next_point, scan[1])
                else:
                    # 右邊的邊，更新右端點
                    next_point = None
                    if current_edge.right_point not in scan:
                            next_point = current_edge.right_point
                    elif current_edge.left_point not in scan:
                            next_point = current_edge.left_point
                    scan = (scan[0], next_point)
            else:
                break
        
        # 補上最後一條 hyperplane
        hyperplane.append((last_intersection, perp_end))
                
        # 移除多餘的邊
        final_edges = self.removeDiscardedEdges(vd_left.edges, vd_right.edges, hyperplane, recorded_edges, intersection_points)
        if hyperplane:
            return VoronoiDiagram(points_left + points_right, final_edges), hyperplane
        else:
            return VoronoiDiagram(points_left + points_right, final_edges)

    def isLinesOverlap(self, line1, line2):
        """ 判斷兩條線段是否重疊 """
        # 提取線段的點
        (x1, y1), (x2, y2) = line1
        (x3, y3), (x4, y4) = line2

        # 計算斜率和截距
        def get_slope_intercept(x1, y1, x2, y2):
            if x1 == x2:  # 垂直線
                return float('inf'), x1  # 用 x1 表示截距
            slope = (y2 - y1) / (x2 - x1)
            intercept = y1 - slope * x1
            return slope, intercept

        slope1, intercept1 = get_slope_intercept(x1, y1, x2, y2)
        slope2, intercept2 = get_slope_intercept(x3, y3, x4, y4)

        # 判斷是否斜率和截距相同（或均為垂直線且 x 坐標相同）
        if slope1 != slope2 or intercept1 != intercept2:
            return False

        # 判斷線段範圍是否重疊
        def is_range_overlap(a1, a2, b1, b2):
            return max(a1, b1) <= min(a2, b2)

        if slope1 == float('inf'):  # 垂直線，只需判斷 y 範圍是否重疊
            return is_range_overlap(y1, y2, y3, y4)
        else:  # 判斷 x 範圍是否重疊
            return is_range_overlap(x1, x2, x3, x4)

    def calculateLineABC(self, p1, p2):
        """ 計算直線方程式的 A, B, C"""
        x1, y1 = p1
        x2, y2 = p2
        a = y1 - y2
        b = x2 - x1
        c = x1 * y2 - x2 * y1
        return a, b, c

    def evaluatePoint(self, point, hyperplane_coeffs, epsilon=1e-9):
        """ 計算點相對於超平面的方位 """
        A, B, C = hyperplane_coeffs
        x, y = point
        value = A * x + B * y + C
        if value > epsilon:
            return 1  # 有效側
        elif value < -epsilon:
            return -1  # 無效側
        else:
            return 0  # 在超平面上

    def isSegmentOnOneSide(self, edge, coeffs):
        """判斷線段是否完全位於 Hyper Plane 的同一側"""
        value1 = self.evaluatePoint(edge.start_point, coeffs)
        value2 = self.evaluatePoint(edge.end_point, coeffs)
        # 如果兩端點符號相同，表示線段完全在 Hyper Plane 的一側
        return value1 * value2 > 0

    def computeLineIntersection(self, bisector, edge):
        """計算兩條線段的交點"""
        a0, b0, c0 = self.calculateLineABC(bisector[0], bisector[1])
        a1, b1, c1 = self.calculateLineABC(edge.start_point, edge.end_point)
        denominator = a0 * b1 - a1 * b0

        if abs(denominator) == 0:
            return None  # 平行，無交點
        x = (b0 * c1 - b1 * c0) / denominator
        y = (a1 * c0 - a0 * c1) / denominator
        if self.isPointOnEdge((x, y), edge):
            return (x, y)
        return None
    
    def isPointOnEdge(self, point, edge, epsilon=1e-9):
        """檢查點是否在邊上"""
        x, y = point
        x1, y1 = edge.start_point
        x2, y2 = edge.end_point
        # 檢查點是否在直線上（考慮浮點數誤差）
        if abs((x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)) > epsilon:
            return False

        # 檢查點的 x 坐標是否在線段的範圍內
        if not (min(x1, x2) - epsilon <= x <= max(x1, x2) + epsilon):
            return False

        # 檢查點的 y 坐標是否在線段的範圍內
        if not (min(y1, y2) - epsilon <= y <= max(y1, y2) + epsilon):
            return False

        return True

    def checkPointInRange(self, point):
        """檢查點是否在矩形範圍內"""
        x, y = point
        x1, y1, x2, y2 = 0, 0, 600, 600
        return x1 <= x <= x2 and y1 <= y <= y2

    def removeDiscardedEdges(self, left_edges, right_edges, hyperplane_segments, recorded_edges, intersection_points):
        """移除 hyperplane 兩側不需要的邊，保留正確的邊"""
        final_edges = []
        
        # 確保 recorded_edges 和 intersection_points 長度一致
        assert len(recorded_edges) == len(intersection_points), "recorded_edges and intersection_points must have the same length"
        
        # 計算所有 hyperplane 分段的係數
        hyperplane_coeffs = []
        for h1, h2 in hyperplane_segments:
            coeffs = self.calculateLineABC(h1, h2)
            hyperplane_coeffs.append(coeffs)
        
        # 處理 recorded_edges 中的邊，剪裁到交點
        for j, edge in enumerate(recorded_edges):
            intersection = intersection_points[j]
            coeffs = hyperplane_coeffs[j]  # 假設每個 recorded_edge 對應一個 hyperplane 段
            if edge in left_edges and self.isPointOnHyperPlane(intersection, coeffs):
                # 將左邊的邊剪裁到交點
                clipped = Edge(edge.start_point, intersection, edge.left_point, edge.right_point)
                final_edges.append(clipped)
            elif edge in right_edges and self.isPointOnHyperPlane(intersection, coeffs):
                # 將右邊的邊剪裁到交點
                clipped = Edge(intersection, edge.end_point, edge.left_point, edge.right_point)
                final_edges.append(clipped)
        
        # 判斷沒有交點的邊是否需要保留
        recorded_edge_set = set(recorded_edges)
        
    

        # 定義一個函數來判斷邊是否在所有 hyperplane 段的一側
        def is_edge_on_one_side(edge):
            for coeffs in hyperplane_coeffs:
                if not self.isSegmentOnOneSide(edge, coeffs):
                    return False
            return True
        
        # 處理 left_edges
        for l_edge in left_edges:
            if l_edge not in recorded_edge_set:
                # if is_edge_on_one_side(l_edge):
                    final_edges.append(l_edge)
        # 處理 right_edges
        for r_edge in right_edges:
            if r_edge not in recorded_edge_set:
                # if is_edge_on_one_side(r_edge):
                    final_edges.append(r_edge)
        
        # 添加 hyperplane 分段本身
        for h_edge in hyperplane_segments:
            final_edges.append(Edge(h_edge[0], h_edge[1]))
        return final_edges

    
    def isPointOnHyperPlane(self, point, coeffs, epsilon=1e-6):
        """ 判斷點是否在超平面上 """
        A, B, C = coeffs
        x, y = point
        value = A * x + B * y + C
        result = abs(value) < epsilon
        return result



    def showAnswer(self):
        """ 直接用套件看答案 """
        # 清除畫布和相關資料
        self.view.scene().clear()
        self.edges.clear()
        self.view.updateCoordinatesDisplay()
        for point in self.view.points:
            self.view.drawPoint(point)

        if self.is_step_by_step:
            # 如果在Step by Step模式中，直接繪製最終結果，並移除輔助線
            self.is_step_by_step = False
        # 排序點
        sorted(self.view.points, key=lambda p: (p[0], p[1]))
        point = sorted(self.removeOverlappingPoints(self.view.points), key=lambda p: (p[0], p[1]))
        num_points = len(point)
        if num_points == 0:
            QMessageBox.information(self, '提示', '請先添加點。')
            return
        elif num_points == 1:
            QMessageBox.information(self, '提示', '單個點的 Voronoi 圖為整個平面。')
            return
        elif num_points == 2:
            self.drawVoronoiDiagram(self.computeVoronoiForTwoPoints(point))
        elif num_points == 3:
            self.drawVoronoiDiagram(self.computeVoronoiForThreePoints(point))
        else:
            self.seeAnswer(point)
            self.drawConvexHull(self.computeConvexHull(point), color=Qt.black, line_style=Qt.DashLine)

    def seeAnswer(self, points, color=Qt.blue):
        """計算 4 個點以上的 Voronoi 圖"""
        points_array = np.array(points)
        vor = Voronoi(points_array)
            
        for ridgeIdx, (pointidx, simplex) in enumerate(zip(vor.ridge_points, vor.ridge_vertices)):
            p1 = points_array[pointidx[0]]
            p2 = points_array[pointidx[1]]
                
            if -1 not in simplex:
                # 有限邊的情況
                start = vor.vertices[simplex[0]]
                end = vor.vertices[simplex[1]]
                self.view.drawLine(tuple(start), tuple(end))
                self.edges.append((tuple(start), tuple(end)))
            else:
                # 無限邊的情況
                i = simplex.index(-1)
                j = simplex[1-i]
                    
                tangent = p2 - p1
                normal = np.array([-tangent[1], tangent[0]])
                normal = normal / np.linalg.norm(normal)
                    
                midpoint = 0.5 * (p1 + p2)
                if np.dot(points_array.mean(axis=0) - midpoint, normal) > 0:
                    normal = -normal
                
                far_point = vor.vertices[j] + normal * 1200
                
                clipped = clipLineToRect((tuple(vor.vertices[j]), tuple(far_point)), 
                                        (0, 0, 600, 600))
                if clipped:
                    self.view.drawLine(clipped[0], clipped[1], color=color)
                    self.edges.append(clipped)

    def loadInputFile(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, '讀取檔案', '', 'Text Files (*.txt)', options=options)
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    self.point_sets.clear()
                    self.current_set_index = -1
                    content = file.readlines()
                    idx = 0
                    while idx < len(content):
                        line = content[idx].strip()
                        # 跳過空行和註解行
                        if not line or line.startswith('#'):
                            idx += 1
                            continue
                        # 嘗試讀取點的數量
                        try:
                            num_points = int(line)
                            idx += 1
                            points = []
                            for _ in range(num_points):
                                while idx < len(content):
                                    line = content[idx].strip()
                                    idx += 1
                                    if not line or line.startswith('#'):
                                        continue
                                    parts = line.split()
                                    if len(parts) >= 2:
                                        x_str, y_str = parts[0], parts[1]
                                        x, y = float(x_str), float(y_str)
                                        points.append((x, y))
                                        break
                            if points:
                                self.point_sets.append(points)
                        except ValueError:
                            idx += 1
                            continue
                    if self.point_sets:
                        self.current_set_index = 0
                        self.showCurrentSet()
                        QMessageBox.information(self, '成功', f'檔案讀取完成，共讀取 {len(self.point_sets)} 組資料。')
                    else:
                        QMessageBox.warning(self, '錯誤', '未讀取到任何有效的點資料。')
            except Exception as e:
                QMessageBox.warning(self, '錯誤', f'讀取檔案時發生錯誤：{e}')

    def saveOutputFile(self):
        if not self.view.points:
            QMessageBox.information(self, '提示', '沒有點可儲存。')
            return
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self, '儲存檔案', '', 'Text Files (*.txt)', options=options)
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    # 排序點集
                    points_sorted = sorted(self.view.points, key=lambda p: (p[0], p[1]))
                    for p in points_sorted:
                        file.write(f'P {int(p[0])} {int(p[1])}\n')
                    # 取得畫布邊界
                    rect = self.scene.sceneRect()
                    rect = (rect.left(), rect.top(), rect.right(), rect.bottom())
                    # 排序邊集
                    edges_sorted = sorted(self.edges, key=lambda e: (e[0][0], e[0][1], e[1][0], e[1][1]))
                    for e in edges_sorted:
                        clipped_line = clipLineToRect(e, rect)
                        if clipped_line:
                            file.write(f'E {int(clipped_line[0][0])} {int(clipped_line[0][1])} {int(clipped_line[1][0])} {int(clipped_line[1][1])}\n')
                QMessageBox.information(self, '成功', '檔案儲存完成。')
            except Exception as e:
                QMessageBox.warning(self, '錯誤', f'儲存檔案時發生錯誤：{e}')

    def loadResultFile(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, '載入結果', '', 'Text Files (*.txt)', options=options)
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    self.clearScene()
                    for line in file:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        # 處理行中包含註解的情況
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        if line:
                            parts = line.split()
                            if parts[0] == 'P' and len(parts) >= 3:
                                _, x_str, y_str = parts[0], parts[1], parts[2]
                                x, y = float(x_str), float(y_str)
                                self.view.points.append((x, y))
                                self.view.drawPoint((x, y))
                            elif parts[0] == 'E' and len(parts) >= 5:
                                _, x1_str, y1_str, x2_str, y2_str = parts[0], parts[1], parts[2], parts[3], parts[4]
                                x1, y1 = float(x1_str), float(y1_str)
                                x2, y2 = float(x2_str), float(y2_str)
                                self.edges.append(((x1, y1), (x2, y2)))
                                self.view.drawLine((x1, y1), (x2, y2))
                    self.view.updateCoordinatesDisplay()
                    QMessageBox.information(self, '成功', '結果載入完成。')
            except Exception as e:
                QMessageBox.warning(self, '錯誤', f'載入結果時發生錯誤：{e}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VoronoiApp()
    window.show()
    sys.exit(app.exec_())
