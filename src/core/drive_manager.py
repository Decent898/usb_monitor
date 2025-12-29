#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储设备管理器
负责管理 U 盘和存储设备的挂载、文件操作等
"""

import os
import shutil
import subprocess
import platform
import string
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
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return DriveManager._scan_macos_drives()
        elif system == "Windows":
            return DriveManager._scan_windows_drives()
        elif system == "Linux":
            return DriveManager._scan_linux_drives()
        
        return []
    
    @staticmethod
    def _scan_macos_drives() -> List[Dict[str, str]]:
        """扫描 macOS 上的驱动器"""
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
    def _scan_windows_drives() -> List[Dict[str, str]]:
        """扫描 Windows 上的驱动器"""
        drives = []
        
        # 扫描所有磁盘驱动器（A-Z）
        for drive_letter in string.ascii_uppercase:
            drive_path = Path(f"{drive_letter}:/")
            if drive_path.exists():
                try:
                    drive_info = DriveManager._get_drive_info(drive_path)
                    if drive_info:
                        drives.append(drive_info)
                except Exception:
                    pass
        
        return drives
    
    @staticmethod
    def _scan_linux_drives() -> List[Dict[str, str]]:
        """扫描 Linux 上的驱动器"""
        drives = []
        mount_path = Path('/mnt')
        
        if mount_path.exists():
            for mount_point in mount_path.iterdir():
                if mount_point.is_dir():
                    try:
                        drive_info = DriveManager._get_drive_info(mount_point)
                        if drive_info:
                            drives.append(drive_info)
                    except Exception:
                        pass
        
        return drives
    
    @staticmethod
    def _get_drive_info(volume: Path) -> Optional[Dict[str, str]]:
        """
        获取驱动器详细信息
        """
        try:
            # 获取磁盘使用情况
            stat = shutil.disk_usage(str(volume))
            total_gb = stat.total / (1024**3)
            used_gb = stat.used / (1024**3)
            free_gb = stat.free / (1024**3)
            
            # 获取文件系统类型
            filesystem = DriveManager._get_filesystem_type(volume)
            
            # 获取设备名称 (卷标)
            # Windows 下 Path('E:/').name 是空的，需要特殊处理
            name = volume.name
            if not name and platform.system() == "Windows":
                name = DriveManager._get_windows_volume_label(volume)
            
            # 如果还是获取不到，显示为 本地磁盘 (X:)
            if not name:
                if platform.system() == "Windows":
                    name = f"本地磁盘 ({str(volume)[0]}:)"
                else:
                    name = str(volume)

            return {
                'name': name,
                'path': str(volume),
                'filesystem': filesystem if filesystem else "未知",
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
    def _get_windows_volume_label(volume: Path) -> str:
        """获取 Windows 卷标"""
        try:
            drive_letter = str(volume)[0]
            result = subprocess.run(
                f'wmic logicaldisk where name="{drive_letter}:" get VolumeName',
                capture_output=True,
                text=True,
                timeout=2,
                shell=True,
                encoding='gbk'
            )
            if result.returncode == 0:
                # 过滤空行并获取第二行 (第一行是标题 VolumeName)
                lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                if len(lines) > 1:
                    return lines[1]
        except:
            pass
        return ""
    
    @staticmethod
    def _get_filesystem_type(volume: Path) -> str:
        """
        获取文件系统类型
        """
        system = platform.system()
        
        if system == "Darwin":  # macOS
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
        
        elif system == "Windows":
            try:
                # 使用 wmic 获取文件系统类型
                drive_letter = str(volume)[0]
                result = subprocess.run(
                    f'wmic logicaldisk where name="{drive_letter}:" get filesystem',
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=True,
                    encoding='gbk'
                )
                
                if result.returncode == 0:
                    # 更加健壮的解析：去除空行，取第二行
                    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                    if len(lines) > 1:
                        return lines[1]
            except Exception:
                pass
        
        elif system == "Linux":
            try:
                result = subprocess.run(
                    ['df', '-T', str(volume)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        parts = lines[1].split()
                        if len(parts) >= 2:
                            return parts[1] # df -T 输出的第二列是类型
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