"""
PyTacView - 简化版
应用程序入口点
"""
import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """
    应用程序主函数
    """
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
