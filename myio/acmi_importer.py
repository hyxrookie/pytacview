"""
ACMI文件导入器 - 简化版
用于读取和解析ACMI格式文件
"""
import math
import re
from datetime import datetime, timedelta
import numpy as np
import os

import pymap3d

from core.data_engine import Entity, DataEngine

class ACMIImporter:
    """
    ACMI文件导入器
    支持Tacview ACMI 2.1格式（简化版）
    """
    def __init__(self, data_engine):
        self.data_engine = data_engine
        self.reference_time = None
        self.reference_lon_deg = 120.0
        self.reference_lat_deg = 60.0
        self.reference_alt_m = 0.0
    def import_file(self, filepath):
        """
        导入ACMI文件

        参数:
        filepath: ACMI文件路径

        返回:
        bool: 是否成功导入
        """
        if not os.path.exists(filepath):
            print(f"错误：文件 {filepath} 不存在")
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 解析文件头
            if not self._parse_header(lines):
                print("错误：文件头解析失败")
                return False

            # 解析数据部分
            self._parse_data(lines)

            return True

        except Exception as e:
            print(f"导入文件时出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _parse_header(self, lines):
        """解析ACMI文件头部"""
        # 检查文件格式版本
        if len(lines) == 0:
            print("错误：文件为空")
            return False

        file_type_line = lines[0].strip()
        # 添加调试信息
        print(f"首行内容: '{file_type_line}'")
        print(f"首行字符编码: {[ord(c) for c in file_type_line]}")

        # 检查是否有BOM或其他前缀
        if file_type_line.startswith("\ufeff"):
            print("检测到BOM标记，正在移除...")
            file_type_line = file_type_line.replace("\ufeff", "")

        # 检查是否有前导空格
        if file_type_line and not file_type_line.startswith("FileType="):
            # 尝试查找FileType=
            if "FileType=" in file_type_line:
                index = file_type_line.find("FileType=")
                print(f"FileType=在位置{index}处找到，前面的字符是: '{file_type_line[:index]}'")
                # 调整起始位置
                file_type_line = file_type_line[index:]
                print(f"调整后的首行: '{file_type_line}'")

        if not file_type_line.startswith("FileType="):
            print(f"错误：不是以FileType=开头 ('{file_type_line}')")
            return False

        if "acmi" not in file_type_line.lower():
            print(f"不支持的文件类型: {file_type_line}")
            return False

        # 解析参考时间
        for line in lines:
            line = line.strip()

            # 参考时间
            if "ReferenceTime=" in line:
                # 提取ReferenceTime后面的部分
                time_parts = line.split("ReferenceTime=")
                if len(time_parts) < 2:
                    continue

                time_str = time_parts[1].strip()
                try:
                    # 解析ISO格式时间
                    self.reference_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    print(f"找到参考时间: {self.reference_time}")
                except ValueError:
                    try:
                        # 尝试解析其他格式
                        self.reference_time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
                        print(f"找到参考时间(备选格式): {self.reference_time}")
                    except ValueError:
                        print(f"无法解析参考时间: {time_str}")
                        return False

            # 开始找到数据部分（以#开头的行）
            if line.startswith("#"):
                return True

        return False

    def _parse_data(self, lines):
        """解析ACMI数据部分"""
        current_entities = {}  # 当前活跃的实体，键为ID
        current_time = None    # 当前时间戳

        # 跳过文件头部分
        data_start = False
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 找到数据部分的开始（第一个时间戳）
            if line.startswith("#") and not data_start:
                data_start = True

            if not data_start:
                continue

            # 解析时间戳行
            if line.startswith("#"):
                try:
                    # 解析时间（相对于参考时间的秒数）
                    time_str = line[1:].strip()
                    time_offset = float(time_str)
                    current_time = self.reference_time + timedelta(seconds=time_offset)
                    #print(f"处理时间: {current_time}")
                except ValueError as e:
                    print(f"解析时间戳出错: {line}, 错误: {e}")
                    continue

            # 解析实体数据行
            elif line and "," in line and "=" in line:
                try:
                    # 提取实体ID
                    parts = line.split(",", 1)
                    entity_id = parts[0]

                    # 解析实体数据
                    self._parse_entity_data(entity_id, parts[1], current_time, current_entities)
                except Exception as e:
                    print(f"解析实体数据出错: {line}, 错误: {e}")
                    continue

        # 将所有实体添加到数据引擎
        for entity in current_entities.values():
            if entity.trajectory:  # 只添加有轨迹数据的实体
                self.data_engine.add_entity(entity)
                #print(f"添加实体: {entity.name}, 轨迹点数量: {len(entity.trajectory)}")

    def _parse_entity_data(self, entity_id, data, current_time, current_entities):
        """
        解析实体数据行

        参数:
        entity_id: 实体ID
        data: 实体数据部分
        current_time: 当前时间戳
        current_entities: 当前实体字典
        """
        # 检查是否需要创建新实体
        if entity_id not in current_entities:
            # 解析实体属性
            name = None
            color = None
            entity_type = None
            radius = None

            # 查找Name属性
            name_match = re.search(r'Name=([^,]+)', data)
            if name_match:
                name = name_match.group(1)

            # 查找Type属性
            type_match = re.search(r'Type=([^,]+)', data)
            if type_match:
                entity_type = type_match.group(1)

            # 查找Radius属性 (用于爆炸效果)
            radius_match = re.search(r'Radius=([^,]+)', data)
            if radius_match:
                try:
                    radius = float(radius_match.group(1))
                except ValueError:
                    radius = 100  # 默认半径

            # 如果未找到名称，使用ID作为名称
            if not name:
                name = f"Unknown {entity_id}"

            # 查找颜色属性
            color_match = re.search(r'Color=([^,]+)', data)
            if color_match:
                color_name = color_match.group(1)

                # 根据颜色名称设置RGB值
                if color_name.lower() == 'red':
                    color = (1.0, 0.0, 0.0)  # 红色
                elif color_name.lower() == 'blue':
                    color = (0.0, 0.0, 1.0)  # 蓝色
                elif color_name.lower() == 'green':
                    color = (0.0, 1.0, 0.0)  # 绿色
                else:
                    color = (0.7, 0.7, 0.7)  # 默认灰色

            # 创建新实体
            entity = Entity(entity_id, name, entity_type, None)  # 不设置coalition
            entity.color = color

            # 对于爆炸类型，设置特殊属性
            if entity_type and "explosion" in entity_type.lower():
                entity.is_explosion = True
                entity.radius = radius if radius else 300  # 默认爆炸半径
                print(f"创建爆炸实体: {name}, 半径: {entity.radius}")
            elif (entity_id.startswith('A') or entity_id.startswith('B')) and name and "AIM" in name:
                entity.is_missile = True
                print(f"创建导弹实体: {name}")
            else:
                entity.is_aircraft = True
                print(f"创建飞机实体: {name}")

            current_entities[entity_id] = entity
        else:
            entity = current_entities[entity_id]

        # 提取位置数据
        t_match = re.search(r'T=([^,]+)', data)
        if t_match and current_time:
            try:
                t_values = t_match.group(1).split('|')
                if len(t_values) >= 3:
                    # 解析位置坐标
                    lon_deg = float(t_values[0])
                    lat_deg = float(t_values[1])
                    alt_m = float(t_values[2])

                    n, e, d = pymap3d.geodetic2ned(lat_deg, lon_deg, alt_m,
                                                   self.reference_lat_deg,
                                                   self.reference_lon_deg,
                                                   self.reference_alt_m)

                    # 转换为 ENU, X=East, Y=North, Z=Up
                    x = e
                    y = n
                    z = -d

                    # 解析方向（如果有）
                    orientation = None
                    if len(t_values) >= 6:
                        pitch = math.radians(float(t_values[3]))
                        yaw = math.radians(float(t_values[4]))
                        roll = math.radians(float(t_values[5]))
                        orientation = [pitch, yaw, roll]

                    # 添加轨迹点
                    entity.add_point(current_time, [x, y, z], orientation)
                    #print(f"添加轨迹点: {entity.name}, 位置: {[x, y, z]}")
            except ValueError as e:
                print(f"解析位置数据出错: {t_match.group(1)}, 错误: {e}")