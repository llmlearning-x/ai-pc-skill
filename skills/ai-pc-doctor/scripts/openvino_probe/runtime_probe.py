"""OpenVINO 运行时探测：是否安装、版本号。

缺失时不抛异常，返回结构化错误 OPENVINO_NOT_INSTALLED 和引导步骤。
工具本身不自动安装任何软件。
"""

# 引导步骤：由 Agent 向用户解释并征得同意后执行
# 注意：与 skill 根目录 requirements.txt 保持一致
INSTALL_GUIDE = [
    "python -m venv .venv",
    "source .venv/bin/activate  # Windows: .venv\\Scripts\\activate",
    "pip install openvino psutil numpy  # quick/standard 模式所需",
    "pip install openvino-genai modelscope  # full 模式（LLM 实测）所需",
    "  # 国内网络可加镜像: -i https://pypi.tuna.tsinghua.edu.cn/simple",
    "python scripts/doctor.py  # 重新运行体检",
]

ERROR_NOT_INSTALLED = {
    "code": "OPENVINO_NOT_INSTALLED",
    "module": "openvino_probe",
    "message": "未检测到 OpenVINO 运行时。请按引导步骤安装后重新运行。",
    "severity": "error",
}


def run() -> dict:
    try:
        import openvino as ov
        return {
            "installed": True,
            "version": ov.__version__,
        }
    except ImportError:
        return {
            "installed": False,
            "version": None,
            "error": dict(ERROR_NOT_INSTALLED),
            "install_guide": list(INSTALL_GUIDE),
        }
    except Exception as exc:  # 装了但 import 失败（如动态库问题）
        return {
            "installed": False,
            "version": None,
            "error": {
                "code": "OPENVINO_IMPORT_FAILED",
                "module": "openvino_probe",
                "message": f"OpenVINO 已安装但导入失败: {exc}",
                "severity": "error",
            },
            "install_guide": list(INSTALL_GUIDE),
        }
