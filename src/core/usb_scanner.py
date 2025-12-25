#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USB 设备扫描器
负责扫描和解析 USB 设备信息
"""

import subprocess
import json
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
        
        try:
            result = subprocess.run(
                ['system_profiler', 'SPUSBDataType', '-json'],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                USBScanner._parse_usb_data(data, devices)
                
        except subprocess.TimeoutExpired:
            print(f"扫描超时（{timeout}秒）")
        except json.JSONDecodeError:
            print("解析 USB 数据失败")
        except Exception as e:
            print(f"扫描 USB 设备出错: {str(e)}")
            
        return devices
    
    @staticmethod
    def _parse_usb_data(data: dict, devices: list, bus_name: str = "USB") -> None:
        """
        递归解析 USB 设备数据
        
        Args:
            data: USB 数据字典
            devices: 设备列表（用于存储结果）
            bus_name: USB 总线名称
        """
        if 'SPUSBDataType' in data:
            for bus in data['SPUSBDataType']:
                if '_items' in bus:
                    USBScanner._parse_usb_items(
                        bus['_items'], 
                        devices, 
                        bus.get('_name', 'USB')
                    )
    
    @staticmethod
    def _parse_usb_items(items: list, devices: list, bus_name: str = "USB") -> None:
        """
        解析 USB 设备项
        
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
                USBScanner._parse_usb_items(
                    item['_items'], 
                    devices, 
                    item.get('_name', bus_name)
                )
