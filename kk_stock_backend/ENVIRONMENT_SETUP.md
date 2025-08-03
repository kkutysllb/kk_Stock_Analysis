# 环境配置说明

## 问题背景

由于abupy框架在Python 3.12中存在兼容性问题（`collections.Iterable`已移至`collections.abc`），我们需要降级到Python 3.11来确保项目正常运行。

## 解决方案

### 方法一：使用conda环境文件（推荐）

1. **删除现有环境并重建**：
   ```bash
   # 删除现有环境
   conda env remove -n kk_stock -y
   
   # 使用environment.yml创建新环境
   conda env create -f environment.yml
   
   # 激活环境
   conda activate kk_stock
   ```

2. **或者使用自动化脚本**：
   ```bash
   # 运行重建脚本
   ./rebuild_env.sh
   ```

### 方法二：使用pip安装（备选）

如果你更喜欢使用pip管理依赖：

```bash
# 创建Python 3.11虚拟环境
conda create -n kk_stock python=3.11 -y
conda activate kk_stock

# 安装依赖
pip install -r requirements_py311.txt
```

## 文件说明

- `environment.yml`: conda环境配置文件，指定Python 3.11和所有依赖
- `requirements_py311.txt`: Python 3.11兼容的pip依赖文件
- `rebuild_env.sh`: 自动化环境重建脚本
- `requirements.txt`: 原始依赖文件（保留备用）
- `requirements_basic.txt`: 基础依赖文件

## 验证安装

环境重建完成后，验证关键组件：

```bash
# 验证Python版本
python --version  # 应该显示Python 3.11.x

# 验证abupy安装
python -c "import abupy; print('abupy版本:', abupy.__version__)"

# 验证其他关键依赖
python -c "import pandas, numpy, tushare; print('核心依赖正常')"
```

## 故障排除

如果仍然遇到问题：

1. **mplfinance版本问题**：
   如果遇到`No matching distribution found for mplfinance>=0.12.0`错误：
   ```bash
   # 手动安装预发布版本
   pip install mplfinance==0.12.10b0
   ```

2. **清理conda缓存**：
   ```bash
   conda clean --all
   ```

3. **手动安装abupy**：
   ```bash
   pip install abupy==0.4.0 --no-cache-dir
   ```

4. **检查环境变量**：
   ```bash
   echo $CONDA_DEFAULT_ENV
   which python
   ```

5. **分步安装依赖**：
   如果批量安装失败，可以分步安装：
   ```bash
   # 先安装核心依赖
   pip install pandas numpy scipy
   # 再安装可视化依赖
   pip install matplotlib==3.8.4
   pip install mplfinance==0.12.10b0
   # 最后安装量化依赖
   pip install abupy==0.4.0
   ```

6. **使用国内镜像源**：
   如果下载速度慢，可以使用国内镜像：
   ```bash
   pip install -r requirements_py311.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```

## 注意事项

1. **Python版本**：确保使用Python 3.11.x版本
2. **abupy版本**：固定使用abupy==0.4.0版本
3. **mplfinance版本**：使用预发布版本0.12.10b0
4. **依赖冲突**：如遇到依赖冲突，优先使用`requirements_py311.txt`中的版本约束
5. **环境隔离**：建议使用conda环境管理，避免全局Python环境污染

## 常见错误及解决方案

### 错误1：collections.Iterable导入失败
```
ImportError: cannot import name 'Iterable' from 'collections'
```
**解决方案**：确保使用Python 3.11，不要使用3.12

### 错误2：mplfinance安装失败
```
ERROR: No matching distribution found for mplfinance>=0.12.0
```
**解决方案**：使用预发布版本`pip install mplfinance==0.12.10b0`

### 错误3：numpy版本冲突
```
ERROR: Ignored the following versions that require a different python version
```
**解决方案**：使用requirements_py311.txt中指定的版本约束

## 更新日期

2025-01-27: 创建Python 3.11兼容环境配置，修复mplfinance版本问题