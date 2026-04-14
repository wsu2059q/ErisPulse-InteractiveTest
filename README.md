# ErisPulse-InteractiveTest

**ErisPulse 交互式对话与 OneBot12 消息构建器功能测试模块**

<p align="center">
  <img src="https://img.shields.io/badge/ErisPulse-Module-blue?style=flat-square" alt="ErisPulse Module" />
  <img src="https://img.shields.io/badge/Python-3.9+-green?style=flat-square" alt="Python 3.10+" />
</p>

---

## 简介

InteractiveTest 是 [ErisPulse](https://github.com/ErisPulse/ErisPulse) 的功能测试模块，用于验证和演示 ErisPulse SDK 提供的交互式对话能力、OneBot12 消息构建器（SendDSL）、事件系统等功能。适合开发者在接入适配器后快速验证各项功能是否正常工作。

## 功能覆盖

### Echo 事件回显

| 命令 | 说明 |
|------|------|
| `/it.echo` | 单次回显完整事件原始数据（标准化字典 + 平台原始数据 + 消息段） |
| `/it.echo_on` | 开启持续 echo 模式，所有非命令消息自动触发回显 |
| `/it.echo_off` | 关闭持续 echo 模式 |

Echo 输出内容：
- **标准化事件字典** — OneBot12 格式（已过滤 `{platform}_raw` 重复字段）
- **平台原始数据** — 适配器上报的原始事件
- **消息段** — OneBot12 消息段数组

持续 echo 模式通过 storage 持久化，重启后仍然有效。命令消息不会触发 echo（避免死循环）。

### 交互式对话

| 命令 | 说明 |
|------|------|
| `/it.wait_reply` | 等待用户回复（30 秒超时） |
| `/it.wait_reply_validate` | 带输入验证的等待回复（1-100 数字校验） |
| `/it.wait_reply_callback` | 带回调函数的等待回复 |
| `/it.confirm` | 确认对话（内置中英文确认词） |
| `/it.confirm_custom` | 自定义确认词对话 |
| `/it.choose` | 选择菜单 |
| `/it.collect` | 表单收集（多字段 + 校验） |
| `/it.wait_for` | 等待任意事件（群成员变化） |

### 多轮对话

| 命令 | 说明 |
|------|------|
| `/it.survey` | 问卷调查（多轮对话 + 退出机制） |
| `/it.chat` | 自由聊天模式（120 秒超时） |

### OneBot12 消息构建器（SendDSL）

| 命令 | 说明 |
|------|------|
| `/it.send_info` | 查询平台支持的发送方法 |
| `/it.send_detail` | 查询指定发送方法详情（参数、返回类型、文档） |
| `/it.dsl_text` | SendDSL 文本发送 |
| `/it.dsl_at` | SendDSL @用户发送 |
| `/it.dsl_atall` | SendDSL @全体成员 |
| `/it.dsl_reply` | SendDSL 回复消息 |
| `/it.dsl_image` | SendDSL 图片发送 |
| `/it.dsl_using` | 查询平台在线 Bot 列表 |
| `/it.dsl_multi` | SendDSL 组合消息（@ + 回复 + 文本） |
| `/it.reply_methods` | event.reply 各种修饰参数（@ / 回复 / 图片） |

### 事件与诊断

| 命令 | 说明 |
|------|------|
| `/it.event_info` | 查看完整事件信息（结构化摘要） |
| `/it.platform_methods` | 查看平台注册的扩展方法 |
| `/it.bot_status` | 查看所有 Bot 在线状态 |

### 存储系统

| 命令 | 说明 |
|------|------|
| `/it.storage_set <key> <value>` | 存储写入 |
| `/it.storage_get <key>` | 存储读取 |
| `/it.storage_delete <key>` | 存储删除 |
| `/it.storage_transaction` | 事务批量写入 |
| `/it.storage_multi` | 批量写入 |

## 安装

```bash
pip install ErisPulse-InteractiveTest
```

模块将通过 ErisPulse 的插件系统自动加载，无需额外配置。

## 配置

模块首次加载时会自动创建默认配置，也可在 ErisPulse 配置文件中手动指定：

```toml
[InteractiveTest]
test_timeout = 60
max_survey_steps = 5
admin_users = []
```

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `test_timeout` | int | 60 | 交互命令默认超时时间（秒） |
| `max_survey_steps` | int | 5 | 问卷调查最大步数 |
| `admin_users` | list | [] | 管理员用户 ID 列表 |

## 使用

确保已正确安装并配置 ErisPulse 及至少一个适配器，模块会自动注册所有测试命令。发送对应命令即可进行功能测试。

## 许可证

请参阅 [LICENSE](LICENSE) 文件。
