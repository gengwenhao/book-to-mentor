# 发布指南

[English](releasing.md) · [渠道状态](platforms.md)

## 首次配置

启用 GitHub Actions，添加名为 `CLAWHUB_TOKEN` 的仓库 Actions Secret，内容为有权代表 `gengwenhao` 发布的 ClawHub 令牌。不要把令牌写进仓库、命令参数、发布包或 Issue；泄露后应在 ClawHub 撤销并更换。GitHub Release 使用工作流临时 `GITHUB_TOKEN`，CI 无需个人 GitHub 令牌。

ClawHub CLI 的版本固定在 `release.json`。向 ClawHub 发布需要遵守其现行条款（包括 MIT-0 再分发要求）；本仓库本身采用 MIT 协议。只发布有权分发的材料。包中只有指令与工具，不含用户书籍和学习记录。

## 源码与版本约定

- `skills/book-to-mentor/SKILL.md` 是唯一的 Skill 指令源文件。
- 根目录 `scripts/`、`assets/mentor-template*.md`、格式指南和状态契约是可编辑源文件。
- `python scripts/release.py sync` 按白名单把所需文件同步到 `skills/book-to-mentor/`，不要手改生成副本。
- `release.json` 是版本来源，`bump` 同时更新它及两种插件清单。
- `README.md` 面向英文读者，`README.zh-CN.md` 面向中文读者；功能、限制与平台状态需保持一致。

根目录不再保留 `SKILL.md`，避免安装器优先找到不完整的包装入口；真正可独立安装的是嵌套的完整技能目录。

如果 1.0.0 安装仍指向旧根目录入口、宿主无法更新，请按 README 的命令重新安装；先保留本地手改内容，不需要替换已经生成的书籍导师与学习历史。

工作流组件固定到核对过的提交 SHA，并使用 Node 24；运行环境固定为 `ubuntu-24.04`，避免系统版本隐式迁移。升级这些固定版本前应重新审查和测试。

## 准备下个版本

以 1.1.0 之后的 1.1.1 为例，请使用尚未发布、更高的语义版本：

```bash
python scripts/release.py bump 1.1.1
# 在 CHANGELOG.md 补充对应的 ## 1.1.1 段落，检查本次改动。
python -m pip install -r requirements-test.txt
python scripts/release.py check
python -m unittest discover -s tests -v
git add <本次核对过的文件>
git commit -m "Release 1.1.1"
git push origin master
```

日常只改源码、不升版本时，也要执行 `python scripts/release.py sync` 再检查和提交。版本、随包资源、更新日志不一致会阻断 CI。

## 先演练，再正式发布

在 [Actions → Release](https://github.com/gengwenhao/book-to-mentor/actions/workflows/release.yml) 中选择 **Run workflow**，分支选 `master`。手动运行只测试、打包，产出可下载的 `release-payload`，不会创建公开 Release，也不会访问 ClawHub。检查 ZIP、校验和及分发清单。

在已经核对过的 `master` 提交上打标签：

```bash
git tag v1.1.1
git push origin v1.1.1
```

标签必须匹配 `release.json`，其提交必须位于 `origin/master` 历史中。工作流随后：

1. 运行提取、记录、国际化与打包测试，检查版本、资源和本地链接。
2. 构建独立 Skill ZIP、完整插件 ZIP、`manifest.json`、`SHA256SUMS`、更新日志与目录跟进清单。
3. 创建 GitHub Release 并上传附件，拒绝覆盖内容冲突的已有附件。
4. 用临时私有配置向 ClawHub 提交该确切版本的纯文本包，并保存 `clawhub-result.json` 回执附件。

二维码和横幅保留在 GitHub / 插件包中；ClawHub 使用纯文本包，Skill 中保留回到 GitHub 的联系方式。打包白名单排除私人书籍、状态、密钥、无关文件和仓库历史。

## 验证与故障恢复

- 检查每个工作流任务：GitHub Release 成功不代表 ClawHub 同样成功。
- `pending-publication` / `submitted` 表示已受理，**不代表审核通过或公开可安装**，需查看回执和实际条目。
- GitHub 发布可重跑：同名已有附件必须逐字节一致，不一致就停止，不会静默覆盖公开产物。
- ClawHub 出错后，先检查该确切版本是否已经受理，再决定是否重试。不确定结果不能当作没发布；脚本固定传递版本，不会重试时自行加版本号。
- 已公开版本需要修正内容时，发布新版本，不移动旧标签。
- 令牌缺失或过期：更新仓库 Secret，核对版本状态后再重跑失败任务。手动构建演练不需要密钥。
- 如果本地 `dist/v<版本>` 已存在，使用 `--output` 指定另一个构建目录；构建器不会覆盖既有产物。

此流程不自动发社区帖子、不合并 PR、不批准平台审核，也不改动用户已安装的技能。请按生成的清单和[平台跟进表](platforms.md)继续处理。发布版本、目录曝光、用户本地更新是三件不同的事。

参考：[GitHub Actions Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)、[ClawHub 发布文档](https://docs.openclaw.ai/clawhub/cli)。
