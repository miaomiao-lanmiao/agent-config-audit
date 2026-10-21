# 交付说明

## 当前状态

本地项目已完成，分支 `feature/scaffold-agent-config-audit`。
GitHub 建仓、推送功能分支和开 PR 等待浏览器账号授权完成。
未合并到 main，未上传 PyPI，未部署生产服务。

## 选题

选择 **Agent Config Audit**：离线检查 MCP 配置，包含 12 类静态风险提示、
配置变更比较、脱敏报告和 CI 阈值。其范围能在当前机器完整验证。
另两项候选和取舍详见 `research/TOPIC_REPORT.md`：wheel 内容检查功能重叠较多；
Unity 资源审计缺少本机 Unity Editor 和真实工程验证条件。

## 本机三条运行命令

```powershell
cd A:\ColorOSData\agent-config-audit
python -m agent_config_audit scan examples/risky.json --format html -o reports/my-review.html --fail-on none
Start-Process reports/my-review.html
```

输出采用新建模式。再次运行时请给出新的输出文件名。
现成报告为 `reports/risky.html`，安装包位于 `dist/`。

## 验证

- Ruff 通过；mypy 的 8 个源码文件通过。
- 43 项测试通过，另有多组参数化边界用例。
- 风险示例 8 条发现（5 高、3 中），加固示例无当前规则发现。
- Edge 桌面/390px 手机检查通过，无脚本错误和横向溢出。
- wheel/sdist 构建与 Twine 元数据检查通过。
- 全新环境离线安装 wheel，无运行依赖；在源码目录之外调用成功。
- 证据、截图路径和复现方法见 `docs/VERIFICATION.md`。

## 待批准/配置的上线动作

1. GitHub 授权完成后，本任务可按既定需求建公开仓库、推功能分支、开 PR。
2. 由你审查并合并 PR：项目代码进入 main，不自动发布。
3. 配置 PyPI pending/trusted publisher 和 `pypi-release` required reviewers，
   确认仅允许 main 部署；这是首次发布的外部账号设置。
4. 确认后启用 `ACA_PUBLISH_ENABLED`，手动运行发布工作流。
5. 审批 `pypi-release` job：允许 OIDC 认证并将 0.1.0 wheel/sdist 上传 PyPI。

## 未自动执行的动作与限制

未自动合并、上传 PyPI、部署、force push 或删除仓库。
静态检查不运行服务，不审查包内容或运行态工具投毒，不能保证配置安全。
报告保留服务名和 JSON pointer，因此这些标识本身不要包含密钥。
本机没有改变宿主沙箱策略；浏览器验证启用了 Chromium 沙箱与域名白名单。
完整发布步骤及回退方式见 `docs/RELEASE.md`。
