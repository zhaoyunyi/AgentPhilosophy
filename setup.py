"""打包资源使用与同步指纹相同的清单，排除残留文件和本机缓存。"""

import sys
from pathlib import Path

from setuptools import setup

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from agentphilosophy.content import source_files  # noqa: E402

packaged = ROOT / "src/agentphilosophy/default_source"
# sdist 不携带中央仓的 modules，直接以其内置内容源执行同一份清单逻辑。
source = ROOT if (ROOT / "catalog.yaml").is_file() else packaged
data = ["default_source/" + path.relative_to(source).as_posix() for path in source_files(source)]
for relative in data:
    if not (ROOT / "src/agentphilosophy" / relative).is_file():
        raise RuntimeError(
            f"missing packaged resource; run python3 scripts/sync-packaged-source.py --apply: {relative}"
        )
setup(package_data={"agentphilosophy": data})
