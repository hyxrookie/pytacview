"""
主窗口 - 简化版
创建应用程序主界面，整合各组件
"""
from datetime import timedelta

from PyQt5.QtWidgets import (QMainWindow, QAction, QFileDialog, QWidget,
                            QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
                            QPushButton, QToolBar, QStatusBar, QDockWidget)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QIcon

from core.data_engine import DataEngine
from myio.acmi_importer import ACMIImporter
from ui.view_control import ViewControl

class MainWindow(QMainWindow):
    """
    PyTacView主窗口
    """
    def __init__(self):
        super().__init__()
        
        # 创建数据引擎
        self.data_engine = DataEngine()
        
        # 创建UI
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 窗口设置
        self.setWindowTitle("PyTacView - 简化版")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
        # 创建中央窗口部件
        self._create_central_widget()
        
        # 创建控制面板
        self._create_control_panel()
        
    def _create_menu_bar(self):
        """创建菜单栏"""
        # 文件菜单
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        
        # 打开文件动作
        open_action = QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # 退出动作
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        # 重置视图动作
        reset_view_action = QAction("重置视图", self)
        reset_view_action.setShortcut("Ctrl+R")
        reset_view_action.triggered.connect(self._reset_view)
        view_menu.addAction(reset_view_action)
        
        # 显示轨迹动作
        self.show_trails_action = QAction("显示轨迹", self)
        self.show_trails_action.setCheckable(True)
        self.show_trails_action.setChecked(True)
        self.show_trails_action.triggered.connect(self._toggle_trails)
        view_menu.addAction(self.show_trails_action)
        
        # 显示标记动作
        self.show_markers_action = QAction("显示标记", self)
        self.show_markers_action.setCheckable(True)
        self.show_markers_action.setChecked(True)
        self.show_markers_action.triggered.connect(self._toggle_markers)
        view_menu.addAction(self.show_markers_action)
        
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)
        
        # 打开文件按钮
        open_action = QAction("打开文件", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # 播放控制按钮
        self.play_button = QAction("播放", self)
        self.play_button.triggered.connect(self._toggle_play)
        toolbar.addAction(self.play_button)
        
        # 重置按钮
        reset_button = QAction("重置", self)
        reset_button.triggered.connect(self._reset_time)
        toolbar.addAction(reset_button)
        
    def _create_central_widget(self):
        """创建中央窗口部件（3D视图）"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建3D视图控制器
        self.view_control = ViewControl(self.data_engine)
        layout.addWidget(self.view_control)
        
        # 创建时间控制条
        time_control_layout = QHBoxLayout()
        
        # 时间标签
        self.time_label = QLabel("时间: --:--:--")
        time_control_layout.addWidget(self.time_label)
        
        # 时间滑块
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setEnabled(False)
        self.time_slider.setTickPosition(QSlider.TicksBelow)
        self.time_slider.setTickInterval(10)
        self.time_slider.valueChanged.connect(self._time_slider_changed)
        time_control_layout.addWidget(self.time_slider)
        
        layout.addLayout(time_control_layout)
        
    def _create_control_panel(self):
        """创建控制面板（停靠窗口）"""
        # 创建停靠窗口
        control_dock = QDockWidget("控制面板", self)
        control_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # 创建控制面板部件
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # 播放速度控制
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("播放速度:"))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100)  # 1x - 100x
        self.speed_slider.setValue(10)      # 默认10x
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(10)
        self.speed_slider.valueChanged.connect(self._speed_slider_changed)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("10x")
        speed_layout.addWidget(self.speed_label)
        
        control_layout.addLayout(speed_layout)
        
        # 轨迹长度控制
        trail_layout = QHBoxLayout()
        trail_layout.addWidget(QLabel("轨迹长度:"))
        
        self.trail_slider = QSlider(Qt.Horizontal)
        self.trail_slider.setRange(1, 300)  # 1-300秒
        self.trail_slider.setValue(30)      # 默认30秒
        self.trail_slider.setTickPosition(QSlider.TicksBelow)
        self.trail_slider.setTickInterval(30)
        self.trail_slider.valueChanged.connect(self._trail_slider_changed)
        trail_layout.addWidget(self.trail_slider)
        
        self.trail_label = QLabel("30秒")
        trail_layout.addWidget(self.trail_label)
        
        control_layout.addLayout(trail_layout)
        
        # 标记大小控制
        marker_layout = QHBoxLayout()
        marker_layout.addWidget(QLabel("标记大小:"))
        
        self.marker_slider = QSlider(Qt.Horizontal)
        self.marker_slider.setRange(1, 20)  # 1-20点大小
        self.marker_slider.setValue(5)      # 默认5
        self.marker_slider.setTickPosition(QSlider.TicksBelow)
        self.marker_slider.setTickInterval(2)
        self.marker_slider.valueChanged.connect(self._marker_slider_changed)
        marker_layout.addWidget(self.marker_slider)
        
        self.marker_label = QLabel("5")
        marker_layout.addWidget(self.marker_label)
        
        control_layout.addLayout(marker_layout)
        
        # 添加伸缩因子（填充剩余空间）
        control_layout.addStretch(1)
        
        # 设置控制面板部件
        control_dock.setWidget(control_widget)
        
        # 添加停靠窗口到主窗口
        self.addDockWidget(Qt.RightDockWidgetArea, control_dock)
        
    def open_file(self):
        """打开ACMI文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开ACMI文件", "", "ACMI文件 (*.acmi *.txt);;所有文件 (*)"
        )
        
        if file_path:
            # 重置数据引擎
            self.data_engine = DataEngine()
            
            # 创建导入器
            importer = ACMIImporter(self.data_engine)
            
            # 导入文件
            self.statusBar.showMessage(f"正在导入文件: {file_path}")
            success = importer.import_file(file_path)
            
            if success:
                # 更新视图控制器的数据引擎
                self.view_control.data_engine = self.data_engine
                
                # 更新时间滑块
                self._update_time_controls()
                
                # 启用时间滑块
                self.time_slider.setEnabled(True)
                
                # 重置视图
                self.view_control.reset_view()
                
                # 更新状态栏
                self.statusBar.showMessage(f"已成功导入文件: {file_path}")
            else:
                self.statusBar.showMessage(f"导入文件失败: {file_path}")
                
    def _update_time_controls(self):
        """更新时间控制"""
        start_time, end_time = self.data_engine.get_time_range()
        
        if start_time and end_time:
            # 计算总时间范围（秒）
            total_seconds = (end_time - start_time).total_seconds()
            
            # 设置滑块范围（使用1000作为最大值，实现毫秒级精度）
            self.time_slider.setRange(0, int(total_seconds * 10))
            
            # 更新时间标签
            self._update_time_label()
        
    def _update_time_label(self):
        """更新时间标签"""
        if self.data_engine.current_time:
            time_str = self.data_engine.current_time.strftime("%H:%M:%S")
            self.time_label.setText(f"时间: {time_str}")
            
    def _time_slider_changed(self, value):
        """时间滑块值变化处理函数"""
        start_time, _ = self.data_engine.get_time_range()
        
        if start_time:
            # 计算新时间（秒）
            seconds = value / 10.0
            new_time = start_time + timedelta(seconds=seconds)
            
            # 设置新时间
            self.data_engine.set_time(new_time)
            
            # 更新时间标签
            self._update_time_label()
            
            # 更新视图
            self.view_control.update()
            
    def _speed_slider_changed(self, value):
        """播放速度滑块值变化处理函数"""
        speed = value
        self.speed_label.setText(f"{speed}x")
        self.view_control.set_play_speed(speed)
        
    def _trail_slider_changed(self, value):
        """轨迹长度滑块值变化处理函数"""
        seconds = value
        self.trail_label.setText(f"{seconds}秒")
        self.view_control.set_trail_length(seconds)
        
    def _marker_slider_changed(self, value):
        """标记大小滑块值变化处理函数"""
        size = value
        self.marker_label.setText(f"{size}")
        self.view_control.set_marker_size(size)
        
    def _toggle_play(self):
        """切换播放/暂停状态"""
        self.view_control.toggle_play()
        
        # 更新按钮文本
        if self.view_control.is_playing:
            self.play_button.setText("暂停")
        else:
            self.play_button.setText("播放")
            
    def _reset_time(self):
        """重置时间到开始时间"""
        start_time, _ = self.data_engine.get_time_range()
        
        if start_time:
            # 设置为开始时间
            self.data_engine.set_time(start_time)
            
            # 更新滑块位置
            self.time_slider.setValue(0)
            
            # 更新时间标签
            self._update_time_label()
            
            # 更新视图
            self.view_control.update()
            
    def _reset_view(self):
        """重置视图"""
        self.view_control.reset_view()
        
    def _toggle_trails(self, checked):
        """切换轨迹显示"""
        self.view_control.toggle_trails(checked)
        
    def _toggle_markers(self, checked):
        """切换标记显示"""
        self.view_control.toggle_markers(checked)
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止播放
        if self.view_control.is_playing:
            self.view_control.toggle_play()
            
        # 接受关闭事件
        event.accept()
