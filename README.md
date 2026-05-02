
## 快速部署（后端）
```bash
# 从官方安装poetry（如果未安装）
curl -sSL https://install.python-poetry.org | python3 -
# 验证安装
poetry --version
# 配置国内镜像源（可选）
poetry source add --priority=primary tsinghua https://pypi.tuna.tsinghua.edu.cn/simple/

# 安装Poetry Vscode插件 python-poetry(可选)
https://marketplace.visualstudio.com/items?itemName=zeshuaro.vscode-python-poetry
```
## 后端依赖安装流程
```bash
cd ./src-backend
# 指定pyton(当前项目为python 3.12.X)
poetry env use /path/to/python
# 安装依赖
poetry install
# 或只安装生产依赖
poetry install --no-dev
# 再次检查Python环境
which python
```