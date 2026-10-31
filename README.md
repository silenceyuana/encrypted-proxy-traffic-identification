# 基于机器学习的加密代理流量识别

最新论文位于根目录：基于机器学习的加密代理流量识别_修订版.docx。作者 张校源（ZhangXiaoyuan），ORCID https://orcid.org/0009-0006-6147-9256。

## 实验范围

指标来自公开真实采集记录。JA4Tor 为 NonTor、Tor、Tor-SS、Tor-Trojan、Tor-VMess 五分类；MineShark 为 ShadowsocksR、Trojan、VMess 三分类。两套数据均无法支持 Shadowsocks、VLESS、Trojan、普通 HTTPS 完整四分类。

JA4Tor 原测试集 RF 准确率 92.12%；MineShark 抓包文件隔离测试 SVM 准确率 97.27%；NBMiner 训练、XMRig 测试时 SVM 准确率 46.66%。图表见 results 目录。

## 数据与结果

- data/raw/ja4tor：作者发布的三个 CSV，来源 https://github.com/das-lab/JA4Tor/tree/main/data
- data/raw/MineShark_AE.tar.gz：原始归档，来源 https://zenodo.org/records/13624058
- data/raw/mineshark_subset：原始记录子集及逐文件 SHA-256 清单。
- scripts：特征提取、模型评估、绘图和论文生成脚本。
- results：指标、预测、混淆矩阵、特征、划分和实验清单。
- qa：排版检查文件。

## Windows 复现

已配置环境为 Python 3.12.14。原始文件已保存在本项目，无需重新下载。

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/run_ja4tor_baseline.py
.venv/Scripts/python.exe scripts/run_mineshark_proxy_baseline.py
.venv/Scripts/python.exe scripts/run_mineshark_workload_shift.py
.venv/Scripts/python.exe scripts/plot_workload_shift.py
.venv/Scripts/python.exe scripts/analyze_feature_importance.py
.venv/Scripts/python.exe scripts/build_paper.py
```

如需恢复 MineShark 子集，先运行 download_mineshark.py，再运行 extract_mineshark_subset.py。JA4Tor 三个文件从上述来源下载至 data/raw/ja4tor，原始 SHA-256 见 results/ja4tor/run_manifest.json。固定随机种子为 42；更换软件版本可能产生数值差异。

按文件隔离保证同一原始记录不同时进入训练和测试，但不保证节点或网络环境独立。迁移实验分别进行类内等量抽样。公开 JA4Tor CSV 缺少原始抓包关联，无法重新验证其抓包级独立性。

完整目标四分类仍需带真值标签的 Shadowsocks、VLESS、Trojan 和 HTTPS 抓包，且应控制业务负载并按节点、会话和采集轮次隔离。

## 特征解释与论文更新

analyze_feature_importance.py 只用JA4Tor训练集拟合相同参数的随机森林，复核测试准确率92.12%，输出30项MDI排名和前10名图。MDI可能偏好连续变量，相关特征共享重要性，不可解释为因果关系。流程图同时区分JA4Tor 30项特征和MineShark 20项特征。

署名与仓库链接由paper_metadata.json管理。论文披露Codex参与文稿起草、翻译润色、代码与图表制作，作者需在投稿前审核。

原始大体积数据和第三方源码不重复上传；从上游仓库下载，保留来源链接与哈希。项目仓库收录复现脚本、结果、图表和修订论文。
