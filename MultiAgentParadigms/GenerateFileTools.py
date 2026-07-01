import os
import re
from datetime import datetime
from rich.console import Console

# 全局 Console 实例（开启 record 以记录所有打印）
console = Console(record=True)


def save_console_to_markdown(save_dir: str = "/Users/a6666/learn/agent/charpter4", filename: str = "") -> str:
    """
    一个基于 Rich 的控制台输出转 Markdown 工具
    它会将控制台中所有已打印的内容整理为 Markdown 格式，并保存到本地指定目录。
    """
    print(f"📝 正在执行 [SaveConsole] 控制台内容导出: {save_dir}/{filename}")
    try:
        # 1. 获取记录的纯文本（去除 ANSI 样式）
        plain_text = _console.export_text(clear=False, styles=False)

        if not plain_text.strip():
            return "错误：控制台无任何打印内容，请先调用 console.print() 输出信息。"

        # 2. 转换为 Markdown 格式
        md_content = _convert_to_markdown(plain_text)

        # 3. 创建保存目录
        os.makedirs(save_dir, exist_ok=True)

        # 4. 生成文件名
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"console_output_{timestamp}"

        # 去除文件名中的非法字符
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filepath = os.path.join(save_dir, f"{safe_filename}.md")

        # 5. 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Console Output Export\n\n")
            f.write(f"> 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(md_content)

        return f"成功导出 {len(plain_text)} 字符到 {filepath}（共 {len(md_content.split(chr(10)))} 行）"

    except Exception as e:
        return f"错误：执行控制台导出时出现问题 - {e}"


def clear_console_record() -> str:
    """
    一个基于 Rich 的控制台记录清空工具
    它会清空控制台的输出记录缓冲区，适用于开始新一轮输出记录前调用。
    """
    print(f"🧹 正在执行 [ClearConsole] 清空控制台记录")
    try:
        _console.export_text(clear=True, styles=False)
        return "成功清空控制台记录。"
    except Exception as e:
        return f"错误：清空控制台记录时出现问题 - {e}"


def _convert_to_markdown(text: str) -> str:
    """将纯文本转换为 Markdown 格式（内部辅助函数）"""
    lines = text.split("\n")
    md_lines = []

    for line in lines:
        stripped = line.strip()

        # 已经是 Markdown 标题（# ## ### 等）
        if re.match(r"^#{1,6}\s", stripped):
            md_lines.append(stripped)
        # 全大写且为字母 -> 视为二级标题
        elif (
            len(stripped) > 3
            and stripped.isupper()
            and stripped.replace(" ", "").isalpha()
        ):
            md_lines.append(f"## {stripped}")
        # 全等号 -> Markdown 分割线
        elif stripped and all(c == "=" for c in stripped):
            md_lines.append("\n---\n")
        # 全横线（长度>=3）-> Markdown 分割线
        elif stripped and all(c == "-" for c in stripped) and len(stripped) >= 3:
            md_lines.append("\n---\n")
        else:
            md_lines.append(line)

    return "\n".join(md_lines).strip()