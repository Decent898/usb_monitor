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
        自动根据表头识别列索引，解决列顺序不一致的问题
        """
        results = []
        # 过滤掉空行
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
            parts = line.split(',')
            
            # 确保行长度足够
            if not parts:
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
        优先尝试 wmic，如果失败或无结果，回退到 PowerShell
        """
        initial_count = len(devices)
        
        # --- 尝试 1: WMIC (速度快) ---
        try:
            # 1. 扫描存储设备 (Win32_DiskDrive)
            result = subprocess.run(
                'wmic diskdrive get Caption,Manufacturer,SerialNumber,PNPDeviceID,InterfaceType /format:csv',
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True,
                encoding='gbk',
                errors='ignore'
            )
            
            if result.returncode == 0:
                rows = USBScanner._parse_wmic_output(result.stdout, ['Caption', 'Manufacturer', 'SerialNumber', 'PNPDeviceID', 'InterfaceType'])
                
                for row in rows:
                    name = row.get('Caption', 'Unknown')
                    manufacturer = row.get('Manufacturer', 'N/A')
                    pnp_id = row.get('PNPDeviceID', '')
                    interface = row.get('InterfaceType', '').upper()
                    
                    # 核心判定逻辑：
                    # 1. 接口类型明确为 USB
                    # 2. PNP ID 包含 USBSTOR (传统 USB 大容量存储)
                    # 3. PNP ID 包含 USB (某些 UAS 设备或复合设备)
                    is_usb_device = 'USB' in interface or 'USB' in pnp_id.upper()
                    
                    if not is_usb_device:
                        continue
                    
                    # 优先使用 wmic 返回的 SerialNumber
                    serial = row.get('SerialNumber', '')
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
            excluded_keywords = [
                'root hub', 'generic usb hub', 'host controller', 
                'pcie', 'pci express', 'intel(r)', 'amd',
                'mass storage', 'usb printing support'
            ]
            
            # 如果存储设备很少，尝试扫描其他设备
            if len(devices) < 20:
                result2 = subprocess.run(
                    'wmic path Win32_PnPEntity where "PNPClass=\'USB\'" get Name,Manufacturer,DeviceID /format:csv',
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=True,
                    encoding='gbk',
                    errors='ignore'
                )
                
                if result2.returncode == 0:
                    rows = USBScanner._parse_wmic_output(result2.stdout, ['Name', 'Manufacturer', 'DeviceID'])
                    for row in rows:
                        name = row.get('Name', '')
                        manufacturer = row.get('Manufacturer', 'N/A')
                        device_id = row.get('DeviceID', '')
                        
                        if not name: continue
                        name_lower = name.lower()
                        
                        # 去重：过滤掉已经作为存储设备添加过的设备
                        vid_pid = USBScanner._extract_vid_pid(device_id)
                        if any(d['vid_pid'] == vid_pid and d['vid_pid'] != 'N/A' for d in devices):
                            continue

                        # 白名单逻辑
                        whitelist_keywords = ['keyboard', 'mouse', 'audio', 'video', 'camera', 'webcam', 'bluetooth', '键盘', '鼠标']
                        is_whitelisted = any(k in name_lower for k in whitelist_keywords)

                        if not is_whitelisted:
                            if any(k in name_lower for k in excluded_keywords):
                                continue
                            if any(d['vid_pid'] == vid_pid and d['vid_pid'] != 'N/A' for d in devices):
                                continue
                        
                        serial = USBScanner._extract_serial_from_pnp(device_id)
                        
                        devices.append({
                            'name': name,
                            'manufacturer': manufacturer if manufacturer else 'N/A',
                            'serial': serial,
                            'bus': 'USB',
                            'speed': 'N/A',
                            'vid_pid': vid_pid
                        })
        except Exception:
            pass

        # --- 尝试 2: PowerShell 回退 (如果 WMIC 未找到设备或兼容性差) ---
        # 如果 devices 列表没有变化（即 WMIC 可能失败了），尝试 PowerShell
        if len(devices) == initial_count:
            try:
                USBScanner._scan_windows_via_powershell(devices, timeout)
            except Exception as e:
                print(f"PowerShell 扫描失败: {e}")

    @staticmethod
    def _scan_windows_via_powershell(devices: list, timeout: int) -> None:
        """
        使用 PowerShell 扫描设备 (Win11 兼容性更好)
        """
        # 1. 扫描磁盘驱动器
        cmd_disk = (
            "Get-CimInstance Win32_DiskDrive | "
            "Select-Object Caption,Manufacturer,SerialNumber,PNPDeviceID,InterfaceType | "
            "ConvertTo-Json -Compress"
        )
        
        try:
            # PowerShell 输出一般是 UTF-8 或系统默认，JSON 解析更安全
            result = subprocess.run(
                ["powershell", "-Command", cmd_disk],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='gbk', # 尝试系统默认编码
                errors='ignore'
            )
            
            # 如果输出为空或失败，可能是编码问题，尝试 utf-8
            if not result.stdout.strip():
                 result = subprocess.run(
                    ["powershell", "-Command", cmd_disk],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding='utf-8',
                    errors='ignore'
                )

            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, dict): data = [data] # 单个对象转列表
                    
                    for item in data:
                        name = item.get('Caption', 'Unknown')
                        manufacturer = item.get('Manufacturer', 'N/A')
                        pnp_id = item.get('PNPDeviceID', '')
                        interface = str(item.get('InterfaceType', '')).upper()
                        
                        is_usb_device = 'USB' in interface or 'USB' in str(pnp_id).upper()
                        if not is_usb_device: continue
                        
                        serial = item.get('SerialNumber', '')
                        if not serial or serial == '0':
                            serial = USBScanner._extract_serial_from_pnp(pnp_id)
                            
                        vid_pid = USBScanner._extract_vid_pid(pnp_id)
                        
                        devices.append({
                            'name': name,
                            'manufacturer': manufacturer if manufacturer != '(Standard disk drives)' else 'Generic',
                            'serial': serial,
                            'bus': 'USB Storage',
                            'speed': 'USB 3.0',
                            'vid_pid': vid_pid
                        })
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

        # 2. 扫描 PNP 实体
        cmd_pnp = (
            "Get-CimInstance Win32_PnPEntity -Filter \"PNPClass='USB'\" | "
            "Select-Object Name,Manufacturer,DeviceID | "
            "ConvertTo-Json -Compress"
        )
        
        try:
            result = subprocess.run(
                ["powershell", "-Command", cmd_pnp],
                capture_output=True,
                text=True,
                timeout=5,
                encoding='gbk',
                errors='ignore'
            )
            
            if not result.stdout.strip():
                 result = subprocess.run(
                    ["powershell", "-Command", cmd_pnp],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    encoding='utf-8',
                    errors='ignore'
                )
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, dict): data = [data]
                    
                    excluded_keywords = ['root hub', 'generic usb hub', 'host controller', 'pcie', 'intel(r)', 'amd']
                    
                    for item in data:
                        name = item.get('Name', '')
                        manufacturer = item.get('Manufacturer', 'N/A')
                        device_id = item.get('DeviceID', '')
                        
                        if not name: continue
                        name_lower = name.lower()
                        
                        vid_pid = USBScanner._extract_vid_pid(device_id)
                        if any(d['vid_pid'] == vid_pid and d['vid_pid'] != 'N/A' for d in devices):
                            continue
                            
                        whitelist = ['keyboard', 'mouse', 'audio', 'video', 'camera', 'webcam', 'bluetooth', '键盘', '鼠标']
                        if not any(k in name_lower for k in whitelist):
                            if any(k in name_lower for k in excluded_keywords): continue
                        
                        serial = USBScanner._extract_serial_from_pnp(device_id)
                        
                        devices.append({
                            'name': name,
                            'manufacturer': manufacturer,
                            'serial': serial,
                            'bus': 'USB',
                            'speed': 'N/A',
                            'vid_pid': vid_pid
                        })
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
    
    @staticmethod
    def _scan_macos_devices(devices: list, timeout: int) -> None:
        """
        在 macOS 上扫描 USB 设备
        """
        # 首先获取已挂载的存储设备列表（用于识别存储设备）
        from pathlib import Path
        mounted_volumes = set()
        volumes_path = Path('/Volumes')
        if volumes_path.exists():
            for volume in volumes_path.iterdir():
                if volume.name != 'Macintosh HD' and not volume.name.startswith('.'):
                    mounted_volumes.add(volume.name)
        
        try:
            result = subprocess.run(
                ['system_profiler', 'SPUSBDataType', '-json'],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                USBScanner._parse_macos_usb_data(data, devices, mounted_volumes)
                
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
    def _parse_macos_usb_data(data: dict, devices: list, mounted_volumes: set, bus_name: str = "USB") -> None:
        if 'SPUSBDataType' in data:
            for bus in data['SPUSBDataType']:
                if '_items' in bus:
                    USBScanner._parse_macos_usb_items(
                        bus['_items'], 
                        devices,
                        mounted_volumes,
                        bus.get('_name', 'USB')
                    )
    
    @staticmethod
    def _parse_macos_usb_items(items: list, devices: list, mounted_volumes: set, bus_name: str = "USB") -> None:
        for item in items:
            name = item.get('_name', 'Unknown Device')
            
            # 判断是否为存储设备（多重判断逻辑）
            name_lower = name.lower()
            
            # 方法1: 通过关键词判断（扩展关键词列表）
            storage_keywords = ['mass storage', 'disk', 'storage', 'flash', 'card reader', 
                              'usb drive', 'thumb drive', 'pen drive', 'removable', 'media']
            has_storage_keyword = any(keyword in name_lower for keyword in storage_keywords)
            
            # 方法2: 检查是否有挂载的卷（如果设备名匹配任何挂载卷）
            has_mounted_volume = any(vol.lower() in name_lower or name_lower in vol.lower() 
                                    for vol in mounted_volumes)
            
            # 方法3: 检查是否有 BSD 名称（存储设备通常有这个）
            has_bsd_name = 'bsd_name' in item
            
            # 综合判断
            is_storage = has_storage_keyword or has_mounted_volume or has_bsd_name
            
            device_info = {
                'name': name,
                'manufacturer': item.get('manufacturer', 'N/A'),
                'serial': item.get('serial_num', 'N/A'),
                'bus': 'USB Storage' if is_storage else bus_name,  # 标记存储设备
                'speed': item.get('device_speed', 'N/A'),
                'vid_pid': f"{item.get('vendor_id', 'N/A')}:{item.get('product_id', 'N/A')}"
            }
            devices.append(device_info)
            
            if '_items' in item:
                USBScanner._parse_macos_usb_items(
                    item['_items'], 
                    devices,
                    mounted_volumes,
                    item.get('_name', bus_name)
                )