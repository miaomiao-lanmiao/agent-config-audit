# 选题报告

调研日期：2026-10-22（Asia/Shanghai）。通过搜索工具查阅一手资料，并使用
Playwright 驱动临时 Edge context 读取 GitHub Trending、PyPI 和 Unity 文档。
研究页面状态保存在本机 `research/research-pages.json`，不依赖登录态。
不根据瞬时 star 数判断选题价值，不声称市场上没有同类工具。

| 候选 | 痛点 | 技术栈 | MVP | 演示效果 | 差异化 | 难度 |
| --- | --- | --- | --- | --- | --- | --- |
| Agent Config Audit | 审查 MCP 配置时难以发现启动参数、权限和凭证风险；差异容易夹带敏感值 | Python 标准库、静态 HTML、SARIF | 显式配置扫描、12 类提示、脱敏报告、前后版本对比、CI 阈值 | 一份危险配置 → 8 条发现 → 加固版本无当前规则发现；报告离线打开 | 不启动服务、不联系远端、零运行依赖、稳定规则 ID 和输入摘要；重点放在启动前审查 | 中：解析和规则准确性需要针对性测试 |
| Wheel Release Lens | 发布 wheel 时容易混入缓存、漏掉文件或包含不合适的内容 | Python zipfile/importlib.metadata | 包结构、重复条目、体积、文件类型检查、HTML 报告 | 将问题 wheel 和干净 wheel 做结构差异展示 | 专注 release artifact 的可视化解释；已有成熟工具，新增价值需要进一步验证 | 低到中：核心可做，但同类功能重叠较多 |
| Unity Asset Footprint | 游戏工程资源体积膨胀、重复纹理难定位 | Python 哈希扫描 + Unity C# Editor 导出 | 重复资源、体积榜、引用导出、报告 | 树状体积图和重复文件分组 | 离线报告便于 CI 留档；不自动删资源 | 中到高：可靠引用关系应经过 Unity Asset Database，当前缺少编辑器和真实测试工程 |

## 决策

选择 **Agent Config Audit**。它结合 AI 工具链与防御性配置审查，能在当前
机器完整实现、自动验证和打包。配置变更对比让项目能持续用于 PR 审查。
暂不做 wheel 方向：check-wheel-contents 已有文件检查能力，需要更明确的新需求。
暂不做 Unity 方向：没有 Unity Editor 验证条件；仅凭文件名判断未使用资源会误导用户。

## 一手资料与事实边界

- [GitHub Trending](https://github.com/trending)：探索入口。页面是动态快照，
  不将热度当作需求证明。
- [MCP SECURITY.md](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/SECURITY.md)：
  本地 stdio 进程按宿主权限运行，配置中的命令执行属于预期行为；本工具将
  相关项称为风险提示，避免把协议设计本身描述成漏洞。
- [Snyk Agent Scan](https://github.com/snyk/agent-scan#security-warning)：
  其运行态分析可能启动 stdio 服务或联系远程服务。本项目不评判其优劣，
  将离线配置审查作为更窄的范围；不检测运行态工具投毒。
- [check-wheel-contents / PyPI](https://pypi.org/project/check-wheel-contents/)：
  已覆盖常见 wheel 内容问题，证明第二候选存在明显功能重叠。
- [Unity Asset Database](https://docs.unity3d.com/Manual/AssetDatabase.html)：
  Unity 的资源管理能力是第三候选可靠引用分析需要考虑的基础。
- [GitHub 环境保护](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)：
  仅声明 environment 名称不等于已配置审批，必须检查 required reviewers。
- [PyPA GitHub Actions 发布指南](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)：
  发布采用环境审批与 OIDC trusted publishing，避免长期发布密钥。

包名查询返回未找到不等于拥有发布权，真实发布前仍须确认 PyPI 项目或 pending publisher。
