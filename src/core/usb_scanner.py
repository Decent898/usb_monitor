#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USB 设备扫描器
负责扫描和解析 USB 设备信息
"""

import subprocess
import json
import platform
import re
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
    def _extract_vid_pid(device_id: str) -> str:
        """从设备 ID 中提取 VID:PID"""
        if not device_id:
            return 'N/A'
        
        # 匹配 VID_xxxx 和 PID_xxxx
        vid_match = re.search(r'VID_([0-9A-Fa-f]{4})', device_id, re.IGNORECASE)
        pid_match = re.search(r'PID_([0-9A-Fa-f]{4})', device_id, re.IGNORECASE)
        
        if vid_match and pid_match:
            return f"{vid_match.group(1)}:{pid_match.group(1)}".upper()
        return 'N/A'

    @staticmethod
    def _extract_serial_from_pnp(device_id: str) -> str:
        """尝试从 PNP Device ID 中提取序列号 (通常是最后一部分)"""
        if not device_id:
            return 'N/A'
        try:
            # 格式通常是 USB\VID_xxxx&PID_xxxx\SERIAL_NUMBER
            parts = device_id.split('\\')
            if len(parts) >= 3:
                serial = parts[-1]
                # 如果序列号包含 &，通常表示它是生成的实例 ID 而不是纯硬件序列号
                if '&' not in serial:
                    return serial
        except:
            pass
        return 'N/A'

    @staticmethod
    def _parse_wmic_output(output: str, required_cols: List[str]) -> List[Dict[str, str]]:
        """
        通用解析 WMIC CSV 输出的方法
        自动根据表头识别列索引
        """
        results = []
        lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
        
        if len(lines) < 2:
            return results
            
        # 1. 解析表头，建立 {列名: 索引} 映射
        header = lines[0].split(',')
        # 去除表头可能存在的 BOM 或空白
        header = [h.strip() for h in header]
        
        col_indices = {}
        for col in required_cols:
            try:
                # 查找列名位置
                idx = header.index(col)
                col_indices[col] = idx
            except ValueError:
                # 某些列可能不存在
                col_indices[col] = -1
        
        # 2. 解析数据行
        for line in lines[1:]:
            # 简单的 CSV 分割 (注意：如果字段内容包含逗号，这里会出错，但 WMIC 输出通常较简单)
            parts = line.split(',')
            
            # 确保行长度足够
            if len(parts) < len(header):
                continue
                
            row_data = {}
            for col, idx in col_indices.items():
                if idx != -1 and idx < len(parts):
                    row_data[col] = parts[idx].strip()
                else:
                    row_data[col] = ''
            results.append(row_data)
            
        return results

    @staticmethod
    def _scan_windows_devices(devices: list, timeout: int) -> None:
        """
        在 Windows 上扫描外部 USB 设备
        """
        try:
            # 1. 扫描存储设备 (Win32_DiskDrive)
            result = subprocess.run(
                'wmic diskdrive where "InterfaceType=\'USB\'" get Caption,Manufacturer,SerialNumber,PNPDeviceID /format:csv',
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True,
                encoding='gbk'
            )
            
            if result.returncode == 0:
                rows = USBScanner._parse_wmic_output(result.stdout, ['Caption', 'Manufacturer', 'SerialNumber', 'PNPDeviceID'])
                
                for row in rows:
                    name = row['Caption'] or 'Unknown'
                    manufacturer = row['Manufacturer']
                    pnp_id = row['PNPDeviceID']
                    
                    # 优先使用 wmic 返回的 SerialNumber
                    serial = row['SerialNumber']
                    if not serial or serial == '0' or len(serial) < 2:
                         serial = USBScanner._extract_serial_from_pnp(pnp_id)
                    
                    vid_pid = USBScanner._extract_vid_pid(pnp_id)
                    
                    devices.append({
                        'name': name,
                        'manufacturer': manufacturer if manufacturer and manufacturer != '(Standard disk drives)' else 'Generic',
                        'serial': serial,
                        'bus': 'USB Storage',
                        'speed': 'USB 3.0',
                        'vid_pid': vid_pid
                    })

            # 2. 补充查询其他 USB 设备 (Win32_PnPEntity)
            # 极大精简了过滤列表，只保留最底层的系统控制器
            excluded_keywords = [
                'root hub', 'generic usb hub', 'host controller',
                'pcie', 'pci express', 'intel(r)', 'amd'
                # 移除了 'composite device', 'input device' 以及所有中文关键词
            ]
            
            if len(devices) < 20:
                result2 = subprocess.run(
                    'wmic path Win32_PnPEntity where "PNPClass=\'USB\'" get Name,Manufacturer,DeviceID /format:csv',
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=True,
                    encoding='gbk'
                )
                
                if result2.returncode == 0:
                    rows = USBScanner._parse_wmic_output(result2.stdout, ['Name', 'Manufacturer', 'DeviceID'])
                    
                    for row in rows:
                        name = row['Name']
                        manufacturer = row['Manufacturer']
                        device_id = row['DeviceID']
                        
                        if not name: continue
                        name_lower = name.lower()
                        
                        # 过滤掉已经作为存储设备添加过的设备
                        vid_pid = USBScanner._extract_vid_pid(device_id)
                        if any(d['vid_pid'] == vid_pid and d['vid_pid'] != 'N/A' for d in devices):
                            continue

                        # 核心逻辑：如果名称明确包含外设关键词，则强制保留
                        whitelist_keywords = ['keyboard', 'mouse', 'audio', 'video', 'camera', 'webcam', 'bluetooth', '键盘', '鼠标']
                        is_whitelisted = any(k in name_lower for k in whitelist_keywords)

                        if not is_whitelisted:
                            # 只有不是白名单设备时，才检查排除列表
                            # 注意：现在排除列表已经很短了，大部分设备都会显示
                            if any(k in name_lower for k in excluded_keywords):
                                continue
                            
                            # 再次确认：如果 VID:PID 与已有存储设备相同，则它是重复的
                            if any(d['vid_pid'] == vid_pid and d['vid_pid'] != 'N/A' for d in devices):
                                continue
                        
                        # 从 DeviceID 提取序列号
                        serial = USBScanner._extract_serial_from_pnp(device_id)
                        
                        devices.append({
                            'name': name,
                            'manufacturer': manufacturer if manufacturer else 'N/A',
                            'serial': serial,
                            'bus': 'USB',
                            'speed': 'N/A',
                            'vid_pid': vid_pid
                        })
                            
        except subprocess.TimeoutExpired:
            print(f"扫描超时（{timeout}秒）")
        except Exception as e:
            print(f"Windows USB 扫描出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    @staticmethod
    def _scan_macos_devices(devices: list, timeout: int) -> None:
        """
        在 macOS 上扫描 USB 设备
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
    def _scan_linux_devices(devices: list, timeout: int) -> None:
        """
        在 Linux 上扫描 USB 设备
        """
        try:
            result = subprocess.run(
                ['lsusb'],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            parts = line.split('ID ')
                            if len(parts) >= 2:
                                meta = parts[0].strip() # Bus 001 Device 002:
                                info = parts[1] # 8087:0024 Intel Corp. Hub
                                
                                vid_pid = info.split(' ', 1)[0]
                                name = info.split(' ', 1)[1] if ' ' in info else 'Unknown'
                                
                                bus_num = meta.split('Bus ')[1].split(' ')[0]
                                
                                devices.append({
                                    'name': name.strip(),
                                    'manufacturer': 'N/A',
                                    'serial': 'N/A',
                                    'bus': f"Bus {bus_num}",
                                    'speed': 'N/A',
                                    'vid_pid': vid_pid
                                })
                        except:
                            pass
                            
        except FileNotFoundError:
            print("找不到 lsusb 命令，请安装 usbutils 包")
        except subprocess.TimeoutExpired:
            print(f"扫描超时（{timeout}秒）")
    
    @staticmethod
    def _parse_macos_usb_data(data: dict, devices: list, bus_name: str = "USB") -> None:
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
            
            if '_items' in item:
                USBScanner._parse_macos_usb_items(
                    item['_items'], 
                    devices, 
                    item.get('_name', bus_name)
                )