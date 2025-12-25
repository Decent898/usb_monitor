#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件传输线程
负责异步文件传输，支持进度显示和速度计算
"""

import os
import time
from PyQt6.QtCore import QThread, pyqtSignal


class FileTransferThread(QThread):
    """文件传输线程类"""
    
    # 信号定义
    progress = pyqtSignal(int, str)  # 进度百分比和传输速度
    finished = pyqtSignal(bool, str)  # 是否成功和消息
    
    def __init__(self, source: str, destination: str, chunk_size: int = 1024 * 1024):
        """
        初始化文件传输线程
        
        Args:
            source: 源文件路径
            destination: 目标文件路径
            chunk_size: 每次读取的块大小（字节），默认 1MB
        """
        super().__init__()
        self.source = source
        self.destination = destination
        self.chunk_size = chunk_size
        self._is_cancelled = False
    
    def run(self):
        """执行文件传输"""
        try:
            file_size = os.path.getsize(self.source)
            start_time = time.time()
            
            with open(self.source, 'rb') as src:
                with open(self.destination, 'wb') as dst:
                    copied = 0
                    
                    while not self._is_cancelled:
                        chunk = src.read(self.chunk_size)
                        if not chunk:
                            break
                        
                        dst.write(chunk)
                        copied += len(chunk)
                        
                        # 计算进度和速度
                        progress_percent = int((copied / file_size) * 100)
                        elapsed = time.time() - start_time
                        
                        if elapsed > 0:
                            speed = (copied / elapsed) / (1024 * 1024)  # MB/s
                            self.progress.emit(progress_percent, f"{speed:.2f} MB/s")
            
            if self._is_cancelled:
                # 如果被取消，删除部分传输的文件
                if os.path.exists(self.destination):
                    os.remove(self.destination)
                self.finished.emit(False, "传输已取消")
            else:
                filename = os.path.basename(self.source)
                self.finished.emit(True, f"文件上传成功: {filename}")
                
        except Exception as e:
            self.finished.emit(False, f"文件传输失败: {str(e)}")
    
    def cancel(self):
        """取消传输"""
        self._is_cancelled = True
