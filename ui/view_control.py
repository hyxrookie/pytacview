"""
视图控制 - 简化版
负责3D渲染和相机控制
"""
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer
import numpy as np
import OpenGL.GL as GL
import OpenGL.GLU as GLU
import math
from datetime import timedelta

class ViewControl(QOpenGLWidget):
    """
    3D视图控制器，负责渲染和相机控制
    """
    def __init__(self, data_engine, parent=None):
        super().__init__(parent)
        self.data_engine = data_engine
        
        # 相机参数
        self.camera_distance = 50000  # 相机距离
        self.camera_azimuth = 0        # 方位角（水平旋转）
        self.camera_elevation = 45     # 仰角（垂直旋转）
        self.camera_target = np.array([0., 0., 0.])  # 相机目标点
        
        # 视图参数
        self.fov = 45.0  # 视野角度
        
        # 鼠标交互参数
        self.last_pos = None
        self.mouse_sensitivity = 0.5  # 鼠标灵敏度
        self.zoom_sensitivity = 0.1   # 缩放灵敏度
        
        # 轨迹渲染参数
        self.trail_length = timedelta(seconds=30)  # 轨迹长度
        self.show_trails = True          # 是否显示轨迹
        self.show_markers = True         # 是否显示标记
        self.marker_size = 5.0           # 标记大小
        
        # 动画参数
        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self.advance_time)
        self.play_speed = 1.0  # 播放速度（倍数）
        self.is_playing = False
        
        # 初始化UI参数
        self.setFocusPolicy(Qt.StrongFocus)  # 允许接收键盘事件
        self.setMouseTracking(True)          # 跟踪鼠标移动
        
    def initializeGL(self):
        """初始化OpenGL环境"""
        # 设置清屏颜色（黑色背景）
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        
        # 启用深度测试
        GL.glEnable(GL.GL_DEPTH_TEST)
        
        # 启用光滑线条
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glHint(GL.GL_LINE_SMOOTH_HINT, GL.GL_NICEST)
        
        # 启用混合
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        
        # 设置点大小
        GL.glPointSize(self.marker_size)
        
    def resizeGL(self, width, height):
        """处理窗口大小变化"""
        # 防止除零错误
        if height == 0:
            height = 1
            
        # 设置视口
        GL.glViewport(0, 0, width, height)
        
        # 设置投影矩阵
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        aspect = width / height
        GLU.gluPerspective(self.fov, aspect, 100.0, 10000000.0)
        
        # 切换回模型视图矩阵
        GL.glMatrixMode(GL.GL_MODELVIEW)
        
    def paintGL(self):
        """渲染3D场景"""
        # 清除缓冲区
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glLoadIdentity()
        
        # 设置相机位置
        self._setup_camera()
        
        # 绘制坐标轴
        self._draw_axes()
        
        # 绘制网格
        self._draw_grid()
        
        # 获取当前时间的实体
        if self.data_engine.current_time:
            # 绘制实体和轨迹
            self._draw_entities()
            
            # 绘制时间信息
            self._draw_time_info()
            
    def _setup_camera(self):
        """设置相机视角"""
        # 计算相机位置（球坐标转笛卡尔坐标）
        azimuth_rad = math.radians(self.camera_azimuth)
        elevation_rad = math.radians(self.camera_elevation)
        
        x = self.camera_distance * math.cos(elevation_rad) * math.sin(azimuth_rad)
        y = self.camera_distance * math.cos(elevation_rad) * math.cos(azimuth_rad)
        z = self.camera_distance * math.sin(elevation_rad)
        
        camera_pos = self.camera_target + np.array([x, y, z])
        
        # 设置视图
        GLU.gluLookAt(
            camera_pos[0], camera_pos[1], camera_pos[2],  # 相机位置
            self.camera_target[0], self.camera_target[1], self.camera_target[2],  # 目标点
            0, 0, 1  # 向上向量（Z轴朝上）
        )
        
    def _draw_axes(self):
        """绘制坐标轴"""
        axis_length = 50000  # 坐标轴长度
        
        GL.glBegin(GL.GL_LINES)
        
        # X轴（红色）
        GL.glColor3f(1.0, 0.0, 0.0)
        GL.glVertex3f(0, 0, 0)
        GL.glVertex3f(axis_length, 0, 0)
        
        # Y轴（绿色）
        GL.glColor3f(0.0, 1.0, 0.0)
        GL.glVertex3f(0, 0, 0)
        GL.glVertex3f(0, axis_length, 0)
        
        # Z轴（蓝色）
        GL.glColor3f(0.0, 0.0, 1.0)
        GL.glVertex3f(0, 0, 0)
        GL.glVertex3f(0, 0, axis_length)
        
        GL.glEnd()
        
    def _draw_grid(self):
        """绘制地面网格"""
        grid_size = 100000  # 网格大小
        grid_step = 10000   # 网格步长
        
        GL.glColor3f(0.3, 0.3, 0.3)  # 灰色
        GL.glBegin(GL.GL_LINES)
        
        # 绘制X方向的线
        for i in range(-grid_size, grid_size + 1, grid_step):
            GL.glVertex3f(i, -grid_size, 0)
            GL.glVertex3f(i, grid_size, 0)
            
        # 绘制Y方向的线
        for i in range(-grid_size, grid_size + 1, grid_step):
            GL.glVertex3f(-grid_size, i, 0)
            GL.glVertex3f(grid_size, i, 0)
            
        GL.glEnd()
        
    def _draw_entities(self):
        """绘制实体和轨迹"""
        current_entities = self.data_engine.get_entities_at_time()
        
        for entity_id, data in current_entities.items():
            entity = data['entity']
            position = data['position']
            
            # 绘制实体标记
            if self.show_markers:
                self._draw_entity_marker(entity, position)
            
            # 绘制轨迹
            if self.show_trails and len(entity.trajectory) > 1:
                self._draw_entity_trail(entity)
                
    def _draw_entity_marker(self, entity, position):
        """绘制实体标记"""
        # 设置实体颜色
        if entity.color:
            GL.glColor3f(*entity.color)
        else:
            GL.glColor3f(1.0, 1.0, 1.0)  # 默认白色
            
        # 绘制点
        GL.glPointSize(self.marker_size)
        GL.glBegin(GL.GL_POINTS)
        GL.glVertex3f(position[0], position[1], position[2])
        GL.glEnd()
        
        # 绘制简单模型（十字形）
        line_size = 1000  # 十字大小
        GL.glBegin(GL.GL_LINES)
        # 水平线
        GL.glVertex3f(position[0] - line_size, position[1], position[2])
        GL.glVertex3f(position[0] + line_size, position[1], position[2])
        # 垂直线
        GL.glVertex3f(position[0], position[1] - line_size, position[2])
        GL.glVertex3f(position[0], position[1] + line_size, position[2])
        # 高度线
        GL.glVertex3f(position[0], position[1], position[2] - line_size)
        GL.glVertex3f(position[0], position[1], position[2] + line_size)
        GL.glEnd()

    def _draw_entity_trail(self, entity):
        # 基本检查
        if not entity.trajectory or not entity.timestamps or len(entity.timestamps) < 1:  # 至少需要一个点来确定当前位置
            return
        if self.data_engine.current_time is None:
            return

        current_t = self.data_engine.current_time
        trail_start_t = current_t - self.trail_length  # trail_length 是 timedelta 对象

        points_to_render = []  # 存储最终要绘制的轨迹点 (np.array)

        # 1. 找到当前时间点实体的位置作为轨迹的绝对终点
        #    get_position_at 应该能正确处理插值
        #    如果实体在 current_t 之前就消失了，get_position_at 会返回最后一个点的位置
        #    如果实体在 current_t 之后才出现，DataEngine.get_entities_at_time 应该已经过滤掉了
        current_pos = entity.get_position_at(current_t)
        if current_pos is None:  # 不太可能发生，因为 get_entities_at_time 应该保证了这一点
            return

        # 2. 从后向前遍历实体轨迹点，收集在 [trail_start_t, current_t] 区间内的点
        #    并且将 current_pos 作为第一个加入的点（轨迹的最新端）
        points_to_render.append(current_pos)

        for i in range(len(entity.timestamps) - 1, -1, -1):
            ts_i = entity.timestamps[i]
            pos_i = entity.trajectory[i]['position']

            if ts_i < trail_start_t:
                # 当前点 ts_i 已经早于轨迹段的起点了
                # 我们需要 ts_i 和它后面一个点 ts_prev (即 entity.timestamps[i+1])
                # 来插值计算出 trail_start_t 时刻的位置
                if i + 1 < len(entity.timestamps):
                    ts_prev = entity.timestamps[i + 1]  # 注意因为是倒序，i+1是时间上更晚的点
                    pos_prev = entity.trajectory[i + 1]['position']

                    # 确保 ts_prev > ts_i 且 trail_start_t 在它们之间
                    if ts_prev > ts_i and trail_start_t > ts_i and trail_start_t < ts_prev:
                        # 插值因子: (trail_start_t - ts_i) / (ts_prev - ts_i)
                        time_diff_total = (ts_prev - ts_i).total_seconds()
                        if time_diff_total > 1e-6:  # 避免除零
                            factor = (trail_start_t - ts_i).total_seconds() / time_diff_total
                            factor = max(0.0, min(1.0, factor))  # 钳位
                            interpolated_start_pos = pos_i + factor * (pos_prev - pos_i)
                            points_to_render.append(interpolated_start_pos)
                break  # 已经到达或超过轨迹段起点，停止收集

            elif ts_i <= current_t:  # 点在 trail_start_t 和 current_t 之间 (或等于 current_t)
                # current_t 的点已经通过 current_pos 加入了
                # 所以这里只加严格小于 current_t 的点，避免重复
                if ts_i < current_t:  # 避免重复添加 current_t 的精确点（如果存在）
                    points_to_render.append(pos_i)
            # else: ts_i > current_t, 忽略这些未来的点 (理论上不应该出现，因为 current_pos 是基于 current_t 的)

        # points_to_render 现在是倒序的 (从 current_t 到 trail_start_t)
        # 我们需要反转它来正确绘制 GL_LINE_STRIP
        points_to_render.reverse()

        if len(points_to_render) < 2:  # 至少需要两个点才能画线
            return

        # 设置绘制颜色
        if entity.color:
            GL.glColor4f(entity.color[0], entity.color[1], entity.color[2], 0.7)  # 半透明
        else:
            GL.glColor4f(1.0, 1.0, 1.0, 0.7)  # 默认白色半透明

        # 绘制轨迹线
        GL.glDisable(GL.GL_TEXTURE_2D)  # 绘制线时通常禁用纹理
        GL.glBegin(GL.GL_LINE_STRIP)
        for point_vec in points_to_render:
            GL.glVertex3fv(point_vec)
        GL.glEnd()
        # GL.glEnable(GL.GL_TEXTURE_2D) # 如果后续有纹理操作，则重新启用
        
    def _draw_time_info(self):
        """绘制时间信息（这里省略，因为在主窗口中已有时间显示）"""
        pass
        
    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        self.last_pos = event.pos()
        
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        if not self.last_pos:
            self.last_pos = event.pos()
            return
            
        # 计算移动差值
        dx = event.x() - self.last_pos.x()
        dy = event.y() - self.last_pos.y()
        
        # 左键拖动：旋转相机
        if event.buttons() & Qt.LeftButton:
            self.camera_azimuth += dx * self.mouse_sensitivity
            self.camera_elevation += dy * self.mouse_sensitivity
            
            # 限制仰角范围（防止翻转）
            self.camera_elevation = max(-89, min(89, self.camera_elevation))
            
            # 规范化方位角
            self.camera_azimuth %= 360
            
        # 右键拖动：平移相机
        elif event.buttons() & Qt.RightButton:
            # 计算平移向量（与相机方向相关）
            azimuth_rad = math.radians(self.camera_azimuth)
            
            # X方向平移（左右）
            x_offset = dx * math.cos(azimuth_rad) - dy * math.sin(azimuth_rad)
            # Y方向平移（前后）
            y_offset = dx * math.sin(azimuth_rad) + dy * math.cos(azimuth_rad)
            
            # 平移系数
            pan_factor = self.camera_distance * 0.001
            
            # 更新相机目标点
            self.camera_target[0] -= x_offset * pan_factor
            self.camera_target[1] -= y_offset * pan_factor
            
        self.last_pos = event.pos()
        self.update()  # 更新视图
        
    def wheelEvent(self, event):
        """处理鼠标滚轮事件（缩放）"""
        zoom_factor = 1.0 - event.angleDelta().y() * 0.001 * self.zoom_sensitivity
        self.camera_distance *= zoom_factor
        
        # 限制缩放范围
        self.camera_distance = max(1000, min(1000000, self.camera_distance))
        
        self.update()  # 更新视图
        
    def keyPressEvent(self, event):
        """处理键盘事件"""
        # 空格键：播放/暂停
        if event.key() == Qt.Key_Space:
            self.toggle_play()
            
        # 方向键：控制时间
        elif event.key() == Qt.Key_Right:
            self.advance_time(5)  # 前进5秒
            
        elif event.key() == Qt.Key_Left:
            self.advance_time(-5)  # 后退5秒
            
        # 重置视图
        elif event.key() == Qt.Key_R:
            self.reset_view()
            
        # 父类处理其他按键
        else:
            super().keyPressEvent(event)
            
    def toggle_play(self):
        """切换播放/暂停状态"""
        if self.is_playing:
            self.play_timer.stop()
            self.is_playing = False
        else:
            # 100ms刷新一次（10fps）
            self.play_timer.start(100)
            self.is_playing = True
            
    def advance_time(self, seconds=None):
        """
        推进时间
        
        参数:
        seconds: 如果指定，则前进指定的秒数；否则根据播放速度前进
        """
        if seconds is None:
            # 根据播放速度计算时间增量（默认每帧0.1秒）
            seconds = 0.1 * self.play_speed
            
        if self.data_engine.current_time:
            self.data_engine.advance_time(seconds)
            
            # 检查是否到达结束时间
            start_time, end_time = self.data_engine.get_time_range()
            if end_time and self.data_engine.current_time > end_time:
                self.data_engine.set_time(start_time)  # 循环播放
                
            self.update()  # 更新视图
            
    def reset_view(self):
        """重置视图参数"""
        self.camera_distance = 100000
        self.camera_azimuth = 0
        self.camera_elevation = 45
        self.camera_target = np.array([0., 0., 0.])
        self.update()
        
    def set_play_speed(self, speed):
        """设置播放速度"""
        self.play_speed = speed
        
    def set_trail_length(self, seconds):
        """设置轨迹长度（秒）"""
        self.trail_length = timedelta(seconds=seconds)
        self.update()
        
    def toggle_trails(self, show):
        """切换是否显示轨迹"""
        self.show_trails = show
        self.update()
        
    def toggle_markers(self, show):
        """切换是否显示标记"""
        self.show_markers = show
        self.update()
        
    def set_marker_size(self, size):
        """设置标记大小"""
        self.marker_size = size
        GL.glPointSize(size)
        self.update()
