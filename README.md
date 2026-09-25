# Chat History Portrait

[English](https://github.com/Collin006/chat-history-portrait/tree/main) | [简体中文](https://github.com/Collin006/chat-history-portrait/tree/zh-CN)

将 ChatGPT 官方导出转化为一份有证据支撑的私密个人画像；只有在用户明确选择后，才进一步生成经过脱敏的可分享身份包。

这是一个 [Codex Skill](https://developers.openai.com/codex/skills/)，面向希望理解自己长期对话轨迹的人：反复出现的问题、工作方式、时间中的变化、创作线索，以及值得被讲述的张力。

它**不是**人格测试、诊断工具，也不是上传聊天记录的云端服务。

## 能做什么

- 在本地读取 ChatGPT 官方导出 ZIP、已解压目录或 `conversations.json`。
- 重建有效对话分支、分配匿名来源索引、建立有大小限制的批次，并支持中断后继续分析。
- 清楚区分：用户直接陈述的事实、长期可观察模式、编辑性解读。
- 要求重要结论提供支持证据、反证、置信度和可推翻条件。
- 先生成私密画像，再记录用户对每一条结论的接受、编辑、拒绝或“仅限私密”决定。
- 提供配方题库：年度版本说明、反复问题、工作方式、有趣矛盾、兴趣演变、未竟之书等。
- 只有在用户明确批准后，才生成经过校验与隐私扫描的公开包。

## 隐私模型

原始导出、规范化语料、来源索引、私密证据和私密报告始终保留在本地。公开包是独立的、经过脱敏的产物，不含原始摘录、来源指针、对话标题或私密时间戳。

只有用户自己写出的消息可作为关于用户的证据。助手消息只能帮助理解上下文，不能作为用户信念、经历或身份的证明。

## 安装

将仓库克隆到 Codex 的 Skills 目录：

```bash
git clone https://github.com/Collin006/chat-history-portrait.git ~/.codex/skills/chat-history-portrait
```

然后在 Codex 中调用：

```text
Use $chat-history-portrait to analyze my ChatGPT export locally and build an evidence-grounded private portrait.
```

### 直接交给 Codex 安装

直接把下面的 GitHub 链接复制给 Codex，再说“帮我安装这个 Skill”：

```text
https://github.com/Collin006/chat-history-portrait

帮我安装这个 Chat History Portrait Skill。
```

如果希望自己安装，也可以使用上面的克隆命令。

## 快速开始

1. 在 ChatGPT 申请官方数据导出：
   - 登录你要分析聊天记录的 ChatGPT 账号，依次点击 **头像菜单 → 设置（Settings）→ 数据控制（Data Controls）→ 导出数据（Export Data）→ 导出（Export）→ 确认导出（Confirm export）**。
   - 等待邮件（或短信）通知，最长可能需要七天；同时检查垃圾邮件和推广邮件文件夹。
   - 保持登录同一个账号，打开通知后点击 **下载数据导出（Download data export）**。下载链接会在 24 小时后失效。
   - 妥善保存下载的 ZIP，它无需解压，可以直接交给这个 Skill 处理。

   如果你的界面文案不同，可查看 [OpenAI 官方导出说明](https://help.openai.com/en/articles/7260999-exporting-your-chatgpt-history-and-data)。
2. 将 ZIP、已解压目录或 `conversations.json` 提供给 Codex，同时准备一个未使用的本地输出目录。
3. Skill 会运行预处理器：

```bash
python3 scripts/prepare_chat_history.py /path/to/export.zip --out /path/to/private-workspace
```

4. 阅读私密画像，并校准其中的结论。
5. 如果希望分享，选择公开范围与身份方式，再在本地生成公开包。

完整流程见 [SKILL.md](SKILL.md)。可从[配方题库](recipes/CATALOG.md)开始挑选想回答的问题和输出形式。

## 仓库结构

```text
SKILL.md                 核心流程与安全边界
recipes/                 内置分析配方声明与题库
references/              证据、隐私、schema 和工作流说明
scripts/                 本地语料预处理与校验工具
```

## 校验

确定性工具不依赖第三方 Python 包：

```bash
python3 scripts/validate_recipes.py
python3 scripts/self_test.py
```

## 贡献原则

欢迎新的配方和渲染器，但必须遵守以下边界：

- 不根据间接聊天证据推断敏感特征、诊断或私密事件。
- “证据不足”是有效结果，不应强行下结论。
- 不在公开结果中放入来源索引、原始摘录或第三方隐私细节。
- 不让任何配方自动发布或上传内容。

## 状态

Skill 正在积极开发中。目前支持 ChatGPT 官方导出和本地、证据驱动的画像生成；网站整合、年度增量导入和社区配方发布仍是后续方向。
