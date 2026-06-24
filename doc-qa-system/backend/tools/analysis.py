import os
import re
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path


def _stamp_charts(stdout: str) -> str:
    """Scan stdout tìm 'chart_saved:<path>', tự rename file thêm timestamp nếu chưa có."""
    ts = int(time.time())
    lines = stdout.splitlines(keepends=True)
    result = []
    for line in lines:
        stripped = line.rstrip("\r\n")
        if stripped.startswith("chart_saved:"):
            old_path = Path(stripped[len("chart_saved:"):].strip())
            if old_path.exists() and not re.search(r"_\d{9,}\.", old_path.name):
                new_path = old_path.with_name(f"{old_path.stem}_{ts}{old_path.suffix}")
                old_path.rename(new_path)
                line = f"chart_saved:{new_path}\n"
        result.append(line)
    return "".join(result)


def _normalize_win_paths(code: str) -> str:
    """Thay backslash trong string literal dạng Windows path ('C:\...') thành forward slash."""
    return re.sub(
        r"(['\"])([A-Za-z]:\\[^'\"]*)\1",
        lambda m: m.group(1) + m.group(2).replace("\\", "/") + m.group(1),
        code,
    )


def run_python_subprocess(code: str, csv_data: str = "") -> str:
    """Chạy code pandas trong subprocess. csv_data là string CSV truyền vào nếu cần."""
    code = _normalize_win_paths(code)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        if csv_data:
            data_file = tmp / "data.csv"
            data_file.write_text(csv_data, encoding="utf-8")
            setup = f"import pandas as pd\ndf = pd.read_csv(r'{data_file}')\n"
        else:
            setup = "import pandas as pd\nimport numpy as np\n"

        user_code = textwrap.dedent(code)
        # Wrap để khi lỗi tự in ra columns của các DataFrame trong scope
        wrapped = (
            "import traceback as _tb\n"
            "import pandas as _pd\n"
            "try:\n"
            + "\n".join("    " + l for l in user_code.splitlines())
            + "\nexcept Exception as _e:\n"
            "    _tb.print_exc()\n"
            "    for _k, _v in list(locals().items()):\n"
            "        if isinstance(_v, _pd.DataFrame) and not _k.startswith('_'):\n"
            "            print(f'[DataFrame \"{_k}\" columns]: {list(_v.columns)}')\n"
        )
        script = tmp / "script.py"
        script.write_text(setup + wrapped, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            timeout=30,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")
        if result.returncode != 0:
            return f"[Lỗi]\n{(stdout + stderr)[:3000]}"
        stdout = _stamp_charts(stdout)
        return stdout[:3000] if stdout.strip() else "[Code chạy thành công nhưng không có output. Dùng print() để hiển thị kết quả.]"


def summarize_statistics(content: str) -> str:
    """Tóm tắt thống kê cơ bản từ nội dung markdown table."""
    code = """
import re, io
import pandas as pd

text = '''__CONTENT__'''

# Tìm và parse markdown table đầu tiên
lines = [l for l in text.split('\\n') if '|' in l]
if not lines:
    print("Không tìm thấy bảng dữ liệu.")
else:
    # Bỏ dòng separator (---)
    data_lines = [l for l in lines if not re.match(r'^[\\s|:-]+$', l)]
    csv_str = '\\n'.join(
        ','.join(c.strip() for c in l.strip().strip('|').split('|'))
        for l in data_lines
    )
    df = pd.read_csv(io.StringIO(csv_str))
    numeric_cols = df.select_dtypes(include='number')
    if not numeric_cols.empty:
        print(numeric_cols.describe().to_string())
    else:
        print("Không có cột số trong bảng.")
""".replace("__CONTENT__", content[:2000].replace("'", "\\'"))

    return run_python_subprocess(code)
