"""
PyTacView核心数据引擎
管理实体和轨迹数据
"""
import numpy as np
from datetime import datetime, timedelta

class Entity:
    """
    表示战术视图中的单个实体（如飞机、舰船等）
    """
    def __init__(self, id, name, type_name=None, coalition=None):
        self.id = id                # 实体唯一标识符
        self.name = name            # 实体名称
        self.type_name = type_name  # 实体类型（如F-16, MiG-29等）
        self.coalition = coalition  # 所属阵营（如红方、蓝方）
        self.trajectory = []        # 轨迹点列表
        self.timestamps = []        # 对应的时间戳
        self.visible = True         # 是否可见
        self.color = None           # 实体颜色

        # 实体类型标志
        self.is_aircraft = False    # 是否为飞机
        self.is_missile = False     # 是否为导弹
        self.is_explosion = False   # 是否为爆炸效果
        self.radius = 100           # 爆炸半径（用于爆炸效果）

    def add_point(self, timestamp, position, orientation=None, velocity=None):
        """
        添加一个轨迹点

        参数:
        timestamp: 时间戳（datetime对象）
        position: 位置坐标 [x, y, z]
        orientation: 朝向 [pitch, yaw, roll]（可选）
        velocity: 速度矢量 [vx, vy, vz]（可选）
        """
        self.timestamps.append(timestamp)
        point = {
            'position': np.array(position, dtype=np.float32),
            'orientation': np.array(orientation, dtype=np.float32) if orientation else None,
            'velocity': np.array(velocity, dtype=np.float32) if velocity else None
        }
        self.trajectory.append(point)

    def get_position_at(self, timestamp):
        """
        获取指定时间的位置（使用线性插值）
        """
        if not self.trajectory:
            return None

        # 如果时间戳小于第一个点或大于最后一个点，则返回最近的点
        if timestamp < self.timestamps[0]:
            return None
        if timestamp > self.timestamps[-1]:
            return self.trajectory[-1]['position']

        # 找到时间戳之间的两个点
        for i in range(len(self.timestamps) - 1):
            if self.timestamps[i] <= timestamp <= self.timestamps[i+1]:
                # 线性插值
                t1, t2 = self.timestamps[i], self.timestamps[i+1]
                p1, p2 = self.trajectory[i]['position'], self.trajectory[i+1]['position']

                # 计算插值因子
                factor = (timestamp - t1).total_seconds() / (t2 - t1).total_seconds()

                # 线性插值计算位置
                return p1 + factor * (p2 - p1)

        return None


class DataEngine:
    """
    管理所有实体和时间数据
    """
    def __init__(self):
        self.entities = {}          # 实体字典，键为ID
        self.start_time = None      # 仿真开始时间
        self.end_time = None        # 仿真结束时间
        self.current_time = None    # 当前仿真时间
        self.reference_point = np.array([0, 0, 0], dtype=np.float32)  # 参考点坐标

    def add_entity(self, entity):
        """添加一个实体"""
        self.entities[entity.id] = entity

        # 更新仿真时间范围
        if entity.timestamps:
            first_time = entity.timestamps[0]
            last_time = entity.timestamps[-1]

            if self.start_time is None or first_time < self.start_time:
                self.start_time = first_time

            if self.end_time is None or last_time > self.end_time:
                self.end_time = last_time

        # 设置当前时间为开始时间（如果未设置）
        if self.current_time is None and self.start_time is not None:
            self.current_time = self.start_time

    def remove_entity(self, entity_id):
        """移除一个实体"""
        if entity_id in self.entities:
            del self.entities[entity_id]

            # 重新计算时间范围
            self._recalculate_time_range()

    def _recalculate_time_range(self):
        """重新计算仿真时间范围"""
        self.start_time = None
        self.end_time = None

        for entity in self.entities.values():
            if not entity.timestamps:
                continue

            first_time = entity.timestamps[0]
            last_time = entity.timestamps[-1]

            if self.start_time is None or first_time < self.start_time:
                self.start_time = first_time

            if self.end_time is None or last_time > self.end_time:
                self.end_time = last_time

    def get_entities_at_time(self, timestamp=None):
        """
        获取指定时间的所有实体位置
        如果未指定时间，则使用当前时间
        """
        if timestamp is None:
            timestamp = self.current_time

        if timestamp is None:
            return {}

        result = {}
        for entity_id, entity in self.entities.items():
            if not entity.visible:
                continue

            position = entity.get_position_at(timestamp)
            if position is not None:
                result[entity_id] = {
                    'entity': entity,
                    'position': position
                }

        return result

    def set_time(self, timestamp):
        """设置当前时间"""
        self.current_time = timestamp

    def advance_time(self, seconds):
        """向前推进时间（秒）"""
        if self.current_time:
            self.current_time += timedelta(seconds=seconds)

    def get_time_range(self):
        """获取时间范围（开始时间和结束时间）"""
        return self.start_time, self.end_time