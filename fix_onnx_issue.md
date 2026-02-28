# 上传失败问题诊断报告

## 问题根源
ONNX Runtime DLL 加载失败，导致 ChromaDB 无法初始化，进而导致文档上传时向量化存储卡住。

错误信息：
```
ImportError: DLL load failed while importing onnxruntime_pybind11_state: 动态链接库(DLL)初始化例程失败。
```

## 解决方案

### 方案 1：安装 Visual C++ Redistributable（推荐）
ONNX Runtime 需要 Microsoft Visual C++ Redistributable。

1. 下载并安装：https://aka.ms/vs/17/release/vc_redist.x64.exe
2. 重启后端服务

### 方案 2：使用不依赖 ONNX 的嵌入方案
修改代码，使用在线 API 或其他嵌入方法，避免使用 ONNX Runtime。

### 方案 3：降级 ONNX Runtime
```bash
cd backend
.\venv\Scripts\pip.exe uninstall onnxruntime -y
.\venv\Scripts\pip.exe install onnxruntime==1.15.1
```

## 临时解决方案（已实施）
我将修改代码使用在线 Embedding API，绕过 ONNX Runtime 问题。
