#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
磁盘测速线程
负责对指定路径进行读写速度测试
"""

import os
import time
import uuid
import platform
import ctypes
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal


class SpeedTestThread(QThread):
    """磁盘测速线程类"""
    
    # 信号: (当前状态文本, 进度0-100)
    progress_update = pyqtSignal(str, int)
    # 信号: (最终结果文本)
    test_finished = pyqtSignal(str)
    # 信号: (错误信息)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, target_path: str, test_size_mb: int = 100):
        """
        初始化测速线程
        
        Args:
            target_path: 测试目标目录 (如 "E:/")
            test_size_mb: 测试文件大小 (MB)，默认为 300MB
        """
        super().__init__()
        self.target_path = Path(target_path)
        self.test_size = test_size_mb * 1024 * 1024  # 转换为字节
        self._is_cancelled = False
        
    def run(self):
        temp_file = self.target_path / f"speed_test_{uuid.uuid4().hex}.tmp"
        # 使用 4MB 缓冲区 (需为扇区大小倍数，4MB通常安全)
        buffer_size = 4 * 1024 * 1024 
        data_chunk = os.urandom(buffer_size)
        
        try:
            # --- 写入测试 ---
            self.progress_update.emit(f"正在准备写入测试 ({self.test_size // (1024*1024)}MB)...", 0)
            
            # 使用 buffering=0 禁用 Python 层面的缓冲
            with open(temp_file, 'wb', buffering=0) as f:
                start_time = time.time()
                bytes_written = 0
                while bytes_written < self.test_size:
                    if self._is_cancelled:
                        break
                    
                    remaining = self.test_size - bytes_written
                    write_len = min(remaining, buffer_size)
                    
                    f.write(data_chunk[:write_len])
                    bytes_written += write_len
                    
                    # 更新进度 (0-50%)
                    percent = int((bytes_written / self.test_size) * 50)
                    self.progress_update.emit(f"写入中... {percent*2}%", percent)
                
                # 关键：强制刷入物理磁盘
                f.flush()
                os.fsync(f.fileno())
            
            write_time = time.time() - start_time
            if write_time == 0: write_time = 0.001
            write_speed = (self.test_size / 1024 / 1024) / write_time
            
            if self._is_cancelled:
                self._cleanup(temp_file)
                return

            # --- 读取测试 ---
            self.progress_update.emit("正在准备读取测试...", 50)
            
            read_speed = 0.0
            
            # 针对 Windows 使用无缓存读取，针对其他系统使用标准读取
            if platform.system() == "Windows":
                read_speed = self._read_windows_uncached(temp_file, buffer_size)
            else:
                read_speed = self._read_standard(temp_file, buffer_size)
            
            # --- 清理 ---
            self._cleanup(temp_file)
            
            if not self._is_cancelled:
                result_text = f"写入: {write_speed:.1f} MB/s | 读取: {read_speed:.1f} MB/s"
                self.test_finished.emit(result_text)
                
        except Exception as e:
            self.error_occurred.emit(f"测试失败: {str(e)}")
            self._cleanup(temp_file)

    def _read_standard(self, file_path, buffer_size):
        """标准读取方法 (Mac/Linux)"""
        start_time = time.time()
        with open(file_path, 'rb', buffering=0) as f:
            bytes_read = 0
            while True:
                if self._is_cancelled: break
                chunk = f.read(buffer_size)
                if not chunk: break
                bytes_read += len(chunk)
                
                percent = 50 + int((bytes_read / self.test_size) * 50)
                self.progress_update.emit(f"读取中... {(percent-50)*2}%", percent)
                
        read_time = time.time() - start_time
        if read_time == 0: read_time = 0.001
        return (bytes_read / 1024 / 1024) / read_time

    def _read_windows_uncached(self, file_path, buffer_size):
        """
        Windows 专用无缓存读取 - 严格类型定义版
        使用 FILE_FLAG_NO_BUFFERING 绕过系统文件缓存
        """
        # Windows API 常量
        GENERIC_READ = 0x80000000
        OPEN_EXISTING = 3
        FILE_ATTRIBUTE_NORMAL = 0x80
        FILE_FLAG_NO_BUFFERING = 0x20000000
        FILE_FLAG_SEQUENTIAL_SCAN = 0x08000000
        INVALID_HANDLE_VALUE = -1
        
        kernel32 = ctypes.windll.kernel32
        
        # --- 关键：定义 ctypes 参数类型，防止 64位 指针截断 ---
        LPVOID = ctypes.c_void_p
        HANDLE = ctypes.c_void_p  # 64位系统下 Handle 是 64 位的
        LPDWORD = ctypes.POINTER(ctypes.c_ulong)
        
        kernel32.CreateFileW.argtypes = [
            ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong, 
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p
        ]
        kernel32.CreateFileW.restype = HANDLE
        
        kernel32.VirtualAlloc.argtypes = [LPVOID, ctypes.c_size_t, ctypes.c_ulong, ctypes.c_ulong]
        kernel32.VirtualAlloc.restype = LPVOID
        
        kernel32.VirtualFree.argtypes = [LPVOID, ctypes.c_size_t, ctypes.c_ulong]
        kernel32.VirtualFree.restype = ctypes.c_int
        
        kernel32.ReadFile.argtypes = [HANDLE, LPVOID, ctypes.c_ulong, LPDWORD, ctypes.c_void_p]
        kernel32.ReadFile.restype = ctypes.c_int
        
        kernel32.CloseHandle.argtypes = [HANDLE]
        kernel32.CloseHandle.restype = ctypes.c_int
        
        # 1. 打开文件
        handle = kernel32.CreateFileW(
            str(file_path),
            GENERIC_READ,
            0, # 不共享
            None,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL | FILE_FLAG_NO_BUFFERING | FILE_FLAG_SEQUENTIAL_SCAN,
            None
        )

        if handle == INVALID_HANDLE_VALUE or handle is None:
            err = ctypes.GetLastError()
            raise Exception(f"无法以无缓存模式打开文件, Error Code: {err}")

        try:
            # 2. 分配对齐的内存
            MEM_COMMIT = 0x1000
            MEM_RESERVE = 0x2000
            PAGE_READWRITE = 0x04
            
            buf_addr = kernel32.VirtualAlloc(
                None, 
                buffer_size, 
                MEM_COMMIT | MEM_RESERVE, 
                PAGE_READWRITE
            )
            
            if not buf_addr:
                raise Exception("内存分配失败")
            
            try:
                bytes_read_cnt = ctypes.c_ulong(0)
                total_read = 0
                
                start_time = time.time()
                
                while total_read < self.test_size:
                    if self._is_cancelled:
                        break
                    
                    to_read = min(buffer_size, self.test_size - total_read)
                    
                    # 必须确保读取大小是扇区对齐的 (通常512或4096)
                    # 由于 buffer_size (4MB) 和 test_size (300MB) 都是 4KB 的倍数，这里通常是安全的
                    
                    success = kernel32.ReadFile(
                        handle,
                        buf_addr,
                        to_read,
                        ctypes.byref(bytes_read_cnt),
                        None
                    )
                    
                    if success == 0: # 失败
                        err = ctypes.GetLastError()
                        if err == 38: # ERROR_HANDLE_EOF (到达文件末尾)
                            break
                        raise Exception(f"ReadFile 失败, Error Code: {err}")
                    
                    if bytes_read_cnt.value == 0:
                        break
                    
                    total_read += bytes_read_cnt.value
                    
                    # 更新进度
                    percent = 50 + int((total_read / self.test_size) * 50)
                    self.progress_update.emit(f"读取中... {(percent-50)*2}%", percent)
                
                read_time = time.time() - start_time
                if read_time == 0: read_time = 0.001
                
                # 使用实际读取的字节数计算速度
                return (total_read / 1024 / 1024) / read_time
                
            finally:
                kernel32.VirtualFree(buf_addr, 0, 0x8000) # MEM_RELEASE
                
        finally:
            kernel32.CloseHandle(handle)

    def _cleanup(self, file_path):
        """清理临时文件"""
        try:
            if file_path.exists():
                os.remove(file_path)
        except:
            pass

    def cancel(self):
        self._is_cancelled = True