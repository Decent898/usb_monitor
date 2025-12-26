#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USB 设备扫描器
负责扫描和解析 USB 设备信息
"""

import subprocess
import json
import platform
from typing import List, Dict, Optional


class USBScanner:
    """USB 设备扫描器类"""
    
    @staticmethod
    def scan_devices(timeout: int = 10) -> List[Dict[str, str]]:
        """
        扫描所有 USB 设备
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            设备信息列表
        """
        devices = []
        system = platform.system()
        
        try:
            if system == "Darwin":  # macOS
                USBScanner._scan_macos_devices(devices, timeout)
            elif system == "Windows":
                USBScanner._scan_windows_devices(devices, timeout)
            elif system == "Linux":
                USBScanner._scan_linux_devices(devices, timeout)
                
        except Exception as e:
            print(f"扫描 USB 设备出错: {str(e)}")
            
        return devices
    
    @staticmethod
    def _scan_macos_devices(devices: list, timeout: int) -> None:
        """
        在 macOS 上扫描 USB 设备
        
        Args:
            devices: 设备列表（用于存储结果）
            timeout: 超时时间（秒）
        """
        try:
            result = subprocess.run(
                ['system_profiler', 'SPUSBDataType', '-json'],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                USBScanner._parse_macos_usb_data(data, devices)
                
        except subprocess.TimeoutExpired:
            print(f"扫描超时（{timeout}秒）")
        except json.JSONDecodeError:
            print("解析 USB 数据失败")
    
    @staticmethod
    def _scan_windows_devices(devices: list, timeout: int) -> None:
        """
        在 Windows 上扫描外部 USB 设备（过滤内部设备）
        
        Args:
            devices: 设备列表（用于存储结果）
            timeout: 超时时间（秒）
        """
        try:
            # 要过滤的内部设备关键词
            internal_keywords = [
                'root hub', 'composite device', 'generic usb hub',
                'input device', 'hid', 'bluetooth', 'wireless',
                'camera', 'webcam', 'audio', 'card reader',
                'usb printing support'
            ]
            
            # 使用更简单快速的查询 - 只查询可移动存储设备
            result = subprocess.run(
                'wmic diskdrive where "InterfaceType=\'USB\'" get Caption,Manufacturer,SerialNumber,PNPDeviceID /format:csv',
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True,
                encoding='gbk'
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # 跳过标题行
                    if line.strip() and ',' in line:
                        try:
                            parts = [p.strip() for p in line.split(',')]
                            if len(parts) >= 3:
                                name = parts[1] if len(parts) > 1 else 'Unknown'
                                manufacturer = parts[2] if len(parts) > 2 else 'N/A'
                                serial = parts[3] if len(parts) > 3 and parts[3] else 'N/A'
                                device_id = parts[4] if len(parts) > 4 else ''
                                
                                # 解析 VID/PID
                                vid_pid = 'N/A'
                                if device_id and 'VID_' in device_id and 'PID_' in device_id:
                                    try:
                                        vid = device_id.split('VID_')[1][:4]
                                        pid = device_id.split('PID_')[1][:4]
                                        vid_pid = f"{vid}:{pid}"
                                    except:
                                        pass
                                
                                if name and name not in ['Caption', '']:
                                    device_info = {
                                        'name': name,
                                        'manufacturer': manufacturer if manufacturer else 'N/A',
                                        'serial': serial,
                                        'bus': 'USB Storage',
                                        'speed': 'USB 2.0/3.0',
                                        'vid_pid': vid_pid
                                    }
                                    devices.append(device_info)
                        except Exception:
                            continue
            
            # 补充查询其他常见的外部USB设备（鼠标、键盘、U盘等）
            if len(devices) < 5:  # 只在设备较少时才补充查询
                result2 = subprocess.run(
                    'wmic path Win32_PnPEntity where "PNPClass=\'USB\'" get Name,Manufacturer,DeviceID /format:csv',
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=True,
                    encoding='gbk'
                )
                
                if result2.returncode == 0:
                    lines = result2.stdout.strip().split('\n')
                    for line in lines[1:]:
                        if line.strip() and ',' in line:
                            try:
                                parts = [p.strip() for p in line.split(',')]
                                if len(parts) >= 3:
                                    name = parts[2] if len(parts) > 2 else ''
                                    manufacturer = parts[1] if len(parts) > 1 else 'N/A'
                                    device_id = parts[3] if len(parts) > 3 else ''
                                    
                                    # 过滤内部设备
                                    if name and not any(keyword in name.lower() for keyword in internal_keywords):
                                        # 解析 VID/PID
                                        vid_pid = 'N/A'
                                        if 'VID_' in device_id and 'PID_' in device_id:
                                            try:
                                                vid = device_id.split('VID_')[1][:4]
                                                pid = device_id.split('PID_')[1][:4]
                                                vid_pid = f"{vid}:{pid}"
                                            except:
                                                pass
                                        
                                        # 避免重复
                                        if not any(d['name'] == name for d in devices):
                                            device_info = {
                                                'name': name,
                                                'manufacturer': manufacturer if manufacturer else 'N/A',
                                                'serial': 'N/A',
                                                'bus': 'USB',
                                                'speed': 'N/A',
                                                'vid_pid': vid_pid
                                            }
                                            devices.append(device_info)
                            except Exception:
                                continue
                            
        except subprocess.TimeoutExpired:
            print(f"扫描超时（{timeout}秒）")
        except Exception as e:
            print(f"Windows USB 扫描出错: {str(e)}")
    
    
    
    @staticmethod
    def _scan_linux_devices(devices: list, timeout: int) -> None:
        """
        在 Linux 上扫描 USB 设备
        
        Args:
            devices: 设备列表（用于存储结果）
            timeout: 超时时间（秒）
        """
        try:
            # 使用 lsusb 命令获取 USB 设备
            result = subprocess.run(
                ['lsusb'],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        # 解析 lsusb 输出格式: Bus 001 Device 002: ID 8087:0024 Intel Corp. Hub
                        try:
                            parts = line.split('ID ')
                            if len(parts) >= 2:
                                device_info = {
                                    'name': parts[1].split(' ', 1)[1] if ' ' in parts[1] else 'Unknown',
                                    'manufacturer': 'N/A',
                                    'serial': 'N/A',
                                    'bus': 'USB',
                                    'speed': 'N/A',
                                    'vid_pid': parts[1].split(' ', 1)[0] if ' ' in parts[1] else parts[1].strip()
                                }
                                devices.append(device_info)
                        except:
                            pass
                            
        except FileNotFoundError:
            print("找不到 lsusb 命令，请安装 usbutils 包")
        except subprocess.TimeoutExpired:
            print(f"扫描超时（{timeout}秒）")
    
    @staticmethod
    def _parse_macos_usb_data(data: dict, devices: list, bus_name: str = "USB") -> None:
        """
        递归解析 macOS USB 设备数据
        
        Args:
            data: USB 数据字典
            devices: 设备列表（用于存储结果）
            bus_name: USB 总线名称
        """
        if 'SPUSBDataType' in data:
            for bus in data['SPUSBDataType']:
                if '_items' in bus:
                    USBScanner._parse_macos_usb_items(
                        bus['_items'], 
                        devices, 
                        bus.get('_name', 'USB')
                    )
    
    @staticmethod
    def _parse_macos_usb_items(items: list, devices: list, bus_name: str = "USB") -> None:
        """
        解析 macOS USB 设备项
        
        Args:
            items: USB 设备项列表
            devices: 设备列表（用于存储结果）
            bus_name: USB 总线名称
        """
        for item in items:
            device_info = {
                'name': item.get('_name', 'Unknown Device'),
                'manufacturer': item.get('manufacturer', 'N/A'),
                'serial': item.get('serial_num', 'N/A'),
                'bus': bus_name,
                'speed': item.get('device_speed', 'N/A'),
                'vid_pid': f"{item.get('vendor_id', 'N/A')}:{item.get('product_id', 'N/A')}"
            }
            devices.append(device_info)
            
            # 递归解析子设备
            if '_items' in item:
                USBScanner._parse_macos_usb_items(
                    item['_items'], 
                    devices, 
                    item.get('_name', bus_name)
                )
