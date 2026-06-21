import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


def run_python_subprocess(code: str, csv_data: str = "") -> str:
    """Chạy code pandas trong subprocess. csv_data là string CSV truyền vào nếu cần."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        if csv_data:
            data_file = tmp / "data.csv"
            data_file.write_text(csv_data, encoding="utf-8")
            setup = f"import pandas as pd\ndf = pd.read_csv(r'{data_file}')\n"
        else:
            setup = "import pandas as pd\nimport numpy as np\n"

        script = tmp / "script.py"
        script.write_text(setup + textwrap.dedent(code), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return f"[Lỗi] {result.stderr[:500]}"
        return result.stdout[:3000]


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
