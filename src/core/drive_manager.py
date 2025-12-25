#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储设备管理器
负责管理 U 盘和存储设备的挂载、文件操作等
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional


class DriveManager:
    """存储设备管理器类"""
    
    @staticmethod
    def scan_mounted_drives() -> List[Dict[str, str]]:
        """
        扫描已挂载的 U 盘
        
        Returns:
            驱动器信息列表
        """
        volumes_path = Path('/Volumes')
        drives = []
        
        if not volumes_path.exists():
            return drives
        
        for volume in volumes_path.iterdir():
            # 跳过系统卷和隐藏卷
            if volume.name == 'Macintosh HD' or volume.name.startswith('.'):
                continue
                
            if volume.is_dir():
                drive_info = DriveManager._get_drive_info(volume)
                if drive_info:
                    drives.append(drive_info)
        
        return drives
    
    @staticmethod
    def _get_drive_info(volume: Path) -> Optional[Dict[str, str]]:
        """
        获取驱动器详细信息
        
        Args:
            volume: 卷路径
            
        Returns:
            驱动器信息字典，如果获取失败则返回 None
        """
        try:
            # 获取磁盘使用情况
            stat = shutil.disk_usage(str(volume))
            total_gb = stat.total / (1024**3)
            used_gb = stat.used / (1024**3)
            free_gb = stat.free / (1024**3)
            
            # 获取文件系统类型
            filesystem = DriveManager._get_filesystem_type(volume)
            
            return {
                'name': volume.name,
                'path': str(volume),
                'filesystem': filesystem,
                'total': f"{total_gb:.2f} GB",
                'used': f"{used_gb:.2f} GB",
                'free': f"{free_gb:.2f} GB",
                'total_bytes': stat.total,
                'used_bytes': stat.used,
                'free_bytes': stat.free
            }
        except Exception as e:
            print(f"获取驱动器信息失败 {volume}: {str(e)}")
            return None
    
    @staticmethod
    def _get_filesystem_type(volume: Path) -> str:
        """
        获取文件系统类型
        
        Args:
            volume: 卷路径
            
        Returns:
            文件系统类型字符串
        """
        try:
            result = subprocess.run(
                ['diskutil', 'info', str(volume)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'File System Personality' in line or 'Type (Bundle)' in line:
                        return line.split(':')[-1].strip()
        except Exception:
            pass
        
        return "Unknown"
    
    @staticmethod
    def list_files(drive_path: str, show_hidden: bool = False) -> List[Dict[str, str]]:
        """
        列出驱动器中的文件
        
        Args:
            drive_path: 驱动器路径
            show_hidden: 是否显示隐藏文件
            
        Returns:
            文件信息列表
        """
        files = []
        path = Path(drive_path)
        
        if not path.exists():
            return files
        
        try:
            for item in path.iterdir():
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                file_info = {
                    'name': item.name,
                    'type': "📁 文件夹" if item.is_dir() else "📄 文件",
                    'size': DriveManager._format_size(item),
                    'path': str(item),
                    'is_dir': item.is_dir()
                }
                files.append(file_info)
        except Exception as e:
            print(f"读取文件列表失败: {str(e)}")
        
        return files
    
    @staticmethod
    def _format_size(path: Path) -> str:
        """
        格式化文件大小
        
        Args:
            path: 文件路径
            
        Returns:
            格式化的大小字符串
        """
        if path.is_dir():
            return "N/A"
        
        try:
            size_bytes = path.stat().st_size
            
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024**2:
                return f"{size_bytes/1024:.2f} KB"
            elif size_bytes < 1024**3:
                return f"{size_bytes/(1024**2):.2f} MB"
            else:
                return f"{size_bytes/(1024**3):.2f} GB"
        except Exception:
            return "N/A"
    
    @staticmethod
    def write_text_file(drive_path: str, filename: str, content: str) -> bool:
        """
        写入文本文件
        
        Args:
            drive_path: 驱动器路径
            filename: 文件名
            content: 文件内容
            
        Returns:
            是否成功
        """
        try:
            file_path = Path(drive_path) / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"写入文件失败: {str(e)}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
            return False
