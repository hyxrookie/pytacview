# PyTacView - 轻量级战术视图显示器

PyTacView是一个用Python实现的轻量级战术视图显示系统，专为显示和分析ACMI格式的飞行数据而设计。该项目提供了一个简单易用的界面，用于可视化飞机、导弹和爆炸等战术事件的轨迹和状态。


## 特性

- **ACMI文件导入**：支持导入和解析标准ACMI格式文件
- **3D可视化**：提供基于OpenGL的交互式3D视图
- **实体跟踪**：追踪并显示飞机、导弹和爆炸等不同类型的实体
- **轨迹分析**：显示飞行轨迹，支持回放和时间控制
- **交互控制**：支持相机旋转、平移和缩放
- **时间控制**：播放、暂停、时间滑块和速度控制

## 系统要求

- Python 3.11
- 依赖库（详见requirements.txt）:
  - NumPy
  - PyOpenGL
  - PyQt5
  - PyQuaternion
  - Matplotlib
  - pymap3d

## 安装

1. 创建虚拟环境(可选):
   ```
    conda create --name pytacview python=3.11
    conda activate pytacview
   ```

2. 安装依赖库:
   ```
   pip install -r requirements.txt
   ```

## 使用方法

1. 运行程序:
   ```
   python run.py
   ```

2. 通过文件菜单打开ACMI文件:
   - 点击 "文件" -> "打开"
   - 选择要分析的ACMI文件

3. 视图交互:
   - 左键拖动: 旋转视图
   - 右键拖动: 平移视图
   - 鼠标滚轮: 缩放视图
   - R键: 重置视图

4. 播放控制:
   - 点击播放按钮或按空格键: 开始/暂停播放
   - 左右方向键: 向前/向后移动时间
   - 时间滑块: 快速跳转到特定时间点

5. 轨迹和标记控制:
   - 在控制面板中调整轨迹长度
   - 调整播放速度
   - 显示或隐藏轨迹和标记

## 项目结构

```
pytacview/
├── core/
│   └── data_engine.py        # 数据处理引擎
├── io/
│   └── acmi_importer.py  # ACMI格式导入器
├── ui/
│   ├── main_window.py        # 主窗口
│   └── view_control.py       # 视图控制(3D渲染)
├── requirements.txt          # 依赖清单
└── run.py                    # 入口点文件
```

## ACMI文件格式

PyTacView支持标准的ACMI 2.1格式文件，文件包含以下主要部分:

1. 文件头: 包含文件类型、版本和参考时间等信息
2. 实体定义: 定义飞机、导弹和其他对象
3. 帧数据: 包含每个时间点各实体的位置和方向信息

支持的实体类型:
- 飞机 (Aircraft)
- 导弹 (Missile)
- 爆炸效果 (Explosion)



## 致谢

- 感谢[Tacview](https://www.tacview.net/)团队开发的ACMI标准
- 本项目使用了PyQt5和PyOpenGL等开源库
