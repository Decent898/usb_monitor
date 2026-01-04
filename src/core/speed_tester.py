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
import subprocess
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

            # --- macOS 特殊处理：清除系统缓存 ---
            if platform.system() == "Darwin":
                self.progress_update.emit("正在清除缓存...", 50)
                print(f"\n[调试] 尝试清除系统缓存...")
                
                try:
                    # 检查是否有 root 权限
                    import os as os_module
                    is_root = os_module.geteuid() == 0
                    
                    if is_root:
                        # 如果是 root 权限，直接执行 purge
                        print(f"[调试] 检测到 root 权限，直接执行 purge")
                        result = subprocess.run(['purge'], timeout=5, check=False,
                                              capture_output=True, text=True)
                        if result.returncode == 0:
                            print(f"[调试] purge 执行成功")
                        else:
                            print(f"[调试] purge 执行失败: {result.stderr}")
                    else:
                        # 非 root 权限，尝试 sudo -n（可能需要密码）
                        print(f"[调试] 非 root 权限，尝试 sudo purge")
                        result = subprocess.run(['sudo', '-n', 'purge'], timeout=5, check=False,
                                              capture_output=True, text=True)
                        if result.returncode == 0:
                            print(f"[调试] sudo purge 执行成功")
                        else:
                            print(f"[调试] sudo purge 失败（建议以管理员身份启动程序）: {result.stderr}")
                            
                except Exception as e:
                    print(f"[调试] 缓存清除异常: {e}")
                
                # 短暂等待让系统处理
                time.sleep(0.3)

            # --- 读取测试 ---
            self.progress_update.emit("正在准备读取测试...", 50)
            
            read_speed = 0.0
            
            # 针对不同系统使用不同方法
            if platform.system() == "Windows":
                read_speed = self._read_windows_uncached(temp_file, buffer_size)
            elif platform.system() == "Darwin":
                # macOS 使用 dd 命令进行真实的无缓存读取
                read_speed = self._read_macos_dd(temp_file)
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
        """标准读取方法 (Mac/Linux) - 使用多种方法绕过缓存"""
        import fcntl
        
        # macOS 特殊处理：尝试清除文件缓存
        if platform.system() == "Darwin":
            try:
                # 方法1: 尝试使用 purge 命令（需要 root 权限，可能失败）
                subprocess.run(['sudo', '-n', 'purge'], timeout=2, check=False, 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
            
            # 方法2: 尝试清除特定文件的缓存
            try:
                # 打开文件，设置 F_NOCACHE，然后立即关闭，清除该文件的缓存
                with open(file_path, 'rb') as f:
                    fcntl.fcntl(f.fileno(), fcntl.F_NOCACHE, 1)
                    # F_RDAHEAD 关闭预读
                    try:
                        fcntl.fcntl(f.fileno(), fcntl.F_RDAHEAD, 0)
                    except:
                        pass
            except:
                pass
            
            # 等待一小段时间，让系统有时间处理
            time.sleep(0.2)
        
        start_time = time.time()
        
        # 重新打开文件进行读取测试
        with open(file_path, 'rb', buffering=0) as f:
            # macOS: 设置 F_NOCACHE 标志绕过文件系统缓存
            if platform.system() == "Darwin":
                try:
                    # F_NOCACHE: 禁用文件缓存
                    result = fcntl.fcntl(f.fileno(), fcntl.F_NOCACHE, 1)
                    if result == -1:
                        self.progress_update.emit("警告: 无法禁用缓存", 50)
                    
                    # F_RDAHEAD: 禁用预读
                    fcntl.fcntl(f.fileno(), fcntl.F_RDAHEAD, 0)
                    
                    # F_GLOBAL_NOCACHE: 全局禁用缓存（如果支持）
                    try:
                        fcntl.fcntl(f.fileno(), 55, 1)  # F_GLOBAL_NOCACHE = 55
                    except:
                        pass
                        
                except Exception as e:
                    self.progress_update.emit(f"警告: 缓存设置失败 - {str(e)}", 50)
            
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

    def _read_macos_dd(self, file_path):
        """
        macOS 专用读取测试 - 使用 dd 命令绕过缓存
        dd 命令可以直接与磁盘交互，避免文件系统缓存
        """
        try:
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            print(f"\n[调试] 文件大小: {file_size / 1024 / 1024:.2f} MB")
            print(f"[调试] 文件路径: {file_path}")
            
            # 尝试清除该文件在内核中的缓存
            try:
                import fcntl
                with open(file_path, 'rb') as f:
                    # F_NOCACHE 标志尝试移除文件的缓存
                    result = fcntl.fcntl(f.fileno(), fcntl.F_NOCACHE, 1)
                    print(f"[调试] F_NOCACHE 设置结果: {result}")
                    # 实际读取一小部分来触发缓存清除
                    f.read(1)
            except Exception as e:
                print(f"[调试] F_NOCACHE 设置失败: {e}")
            
            self.progress_update.emit("使用 dd 命令进行无缓存读取...", 70)
            
            # 使用 dd 命令读取，并计时
            # bs=1m 表示每次读取1MB
            # 不使用 iflag=direct，因为 macOS 的 dd 不支持
            print(f"[调试] 开始执行 dd 命令...")
            start_time = time.time()
            
            result = subprocess.run(
                ['dd', f'if={file_path}', 'of=/dev/null', 'bs=1m'],
                capture_output=True,
                text=True,
                timeout=120  # 最多等待2分钟
            )
            
            read_time = time.time() - start_time
            
            print(f"[调试] dd 命令完成")
            print(f"[调试] dd 返回码: {result.returncode}")
            print(f"[调试] dd stderr 输出:\n{result.stderr}")
            print(f"[调试] dd stdout 输出:\n{result.stdout}")
            print(f"[调试] 读取耗时: {read_time:.3f} 秒")
            
            if read_time == 0: 
                read_time = 0.001
            
            # 计算速度 (MB/s)
            speed_mbps = (file_size / 1024 / 1024) / read_time
            print(f"[调试] 计算速度: {speed_mbps:.2f} MB/s")
            
            self.progress_update.emit("读取完成", 100)
            
            return speed_mbps
            
        except subprocess.TimeoutExpired:
            raise Exception("dd 读取超时")
        except Exception as e:
            raise Exception(f"dd 读取失败: {str(e)}")

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