import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command, message, notice, meta


class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("InteractiveTest")
        self.storage = sdk.storage
        self.config = self._load_config()

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy

        return ModuleLoadStrategy(lazy_load=False, priority=10)

    def _load_config(self):
        config = self.sdk.config.getConfig("InteractiveTest")
        if not config:
            default_config = {
                "test_timeout": 60,
                "max_survey_steps": 5,
                "admin_users": [],
            }
            self.sdk.config.setConfig("InteractiveTest", default_config)
            self.logger.warning("已创建默认配置，请根据需要修改")
            return default_config
        return config

    async def on_load(self, event):
        self._register_commands()
        self._register_message_handlers()
        self._register_notice_handlers()
        self._register_meta_handlers()
        self.logger.info("InteractiveTest 模块已加载")

    async def on_unload(self, event):
        self.logger.info("InteractiveTest 模块已卸载")

    # ============================================================
    # 命令注册
    # ============================================================

    def _register_commands(self):
        self._register_interaction_commands()
        self._register_message_builder_commands()
        self._register_event_info_commands()
        self._register_storage_commands()
        self._register_conversation_commands()

    # ----------------------------------------------------------
    # 交互式对话命令
    # ----------------------------------------------------------

    def _register_interaction_commands(self):
        @command("it.wait_reply", group="InteractiveTest", help="测试等待用户回复")
        async def wait_reply_handler(event):
            await event.reply("[wait_reply] 请在 30 秒内回复任意内容:")
            reply = await event.wait_reply(timeout=30)
            if reply:
                text = reply.get_text()
                user_id = reply.get_user_id()
                await event.reply(
                    f"[wait_reply] 收到来自 {user_id} 的回复: {text}",
                    at_users=[user_id],
                )
            else:
                await event.reply("[wait_reply] 等待超时，未收到回复")

        @command(
            "it.wait_reply_validate",
            group="InteractiveTest",
            help="测试带验证的等待回复",
        )
        async def wait_reply_validate_handler(event):
            def validate_number(evt):
                try:
                    val = int(evt.get_text())
                    return 1 <= val <= 100
                except (ValueError, TypeError):
                    return False

            await event.reply("[validate] 请输入一个 1-100 之间的数字:")
            reply = await event.wait_reply(timeout=30, validator=validate_number)

            if reply:
                number = int(reply.get_text())
                await event.reply(f"[validate] 验证通过! 你输入的数字是: {number}")
            else:
                await event.reply("[validate] 输入无效或等待超时")

        @command(
            "it.wait_reply_callback",
            group="InteractiveTest",
            help="测试带回调的等待回复",
        )
        async def wait_reply_callback_handler(event):
            async def on_reply(reply_event):
                text = reply_event.get_text().lower()
                if text in ["是", "yes", "y", "确认"]:
                    await event.reply("[callback] 回调确认: 已收到你的肯定回复!")
                elif text in ["否", "no", "n", "取消"]:
                    await event.reply("[callback] 回调确认: 已收到你的否定回复!")
                else:
                    await event.reply(f"[callback] 回调确认: 收到未识别的回复 '{text}'")

            await event.reply("[callback] 请回复 '是' 或 '否' (30秒内):")
            await event.wait_reply(timeout=30, callback=on_reply)

        @command("it.confirm", group="InteractiveTest", help="测试确认对话")
        async def confirm_handler(event):
            result = await event.confirm("[confirm] 你确定要执行此操作吗?")
            if result:
                await event.reply("[confirm] 已确认! 操作将执行")
            else:
                await event.reply("[confirm] 已取消操作")

        @command("it.confirm_custom", group="InteractiveTest", help="测试自定义确认词")
        async def confirm_custom_handler(event):
            result = await event.confirm(
                "[confirm_custom] 输入 go 继续, stop 停止:",
                yes_words={"go", "继续", "开始"},
                no_words={"stop", "停止", "取消"},
            )
            if result:
                await event.reply("[confirm_custom] 确认继续!")
            else:
                await event.reply("[confirm_custom] 已停止")

        @command("it.choose", group="InteractiveTest", help="测试选择菜单")
        async def choose_handler(event):
            options = [
                "🔴 红色 - 热情似火",
                "🟢 绿色 - 生机盎然",
                "🔵 蓝色 - 深沉宁静",
                "🟡 黄色 - 温暖明亮",
                "🟣 紫色 - 神秘优雅",
            ]
            choice = await event.choose("[choose] 请选择你喜欢的颜色:", options)

            if choice is not None:
                await event.reply(f"[choose] 你选择了: {options[choice]}")
            else:
                await event.reply("[choose] 选择超时")

        @command("it.collect", group="InteractiveTest", help="测试表单收集")
        async def collect_handler(event):
            fields = [
                {"key": "name", "prompt": "[collect/1/3] 请输入你的姓名:"},
                {
                    "key": "age",
                    "prompt": "[collect/2/3] 请输入你的年龄:",
                    "validator": lambda e: e.get_text().strip().isdigit(),
                },
                {"key": "hobby", "prompt": "[collect/3/3] 请输入你的爱好:"},
            ]

            data = await event.collect(fields)

            if data:
                await event.reply(
                    f"[collect] 收集完成!\n"
                    f"  姓名: {data['name']}\n"
                    f"  年龄: {data['age']}\n"
                    f"  爱好: {data['hobby']}"
                )
                user_id = event.get_user_id()
                self.storage.set(f"itest:profile:{user_id}", data)
            else:
                await event.reply("[collect] 表单收集超时或输入无效")

        @command("it.wait_for", group="InteractiveTest", help="测试等待任意事件")
        async def wait_for_handler(event):
            if not event.is_group_message():
                await event.reply("[wait_for] 此命令仅限群聊使用")
                return

            await event.reply("[wait_for] 正在等待群成员变化事件 (120秒)...")
            evt = await event.wait_for(
                event_type="notice",
                condition=lambda e: (
                    e.get_detail_type()
                    in ("group_member_increase", "group_member_decrease")
                    and e.get_group_id() == event.get_group_id()
                ),
                timeout=120,
            )

            if evt:
                detail = evt.get_detail_type()
                user_id = evt.get_user_id()
                operator_id = evt.get_operator_id()
                if detail == "group_member_increase":
                    await event.reply(
                        f"[wait_for] 检测到新成员加入!\n"
                        f"  新成员: {user_id}\n"
                        f"  邀请人: {operator_id or '未知'}"
                    )
                else:
                    await event.reply(
                        f"[wait_for] 检测到成员离开!\n"
                        f"  离开成员: {user_id}\n"
                        f"  操作者: {operator_id or '未知'}"
                    )
            else:
                await event.reply("[wait_for] 等待超时，未检测到群成员变化")

    # ----------------------------------------------------------
    # 多轮对话命令
    # ----------------------------------------------------------

    def _register_conversation_commands(self):
        @command("it.survey", group="InteractiveTest", help="多轮对话 - 问卷调查")
        async def survey_handler(event):
            conv = event.conversation(timeout=60)

            questions = [
                "你对 ErisPulse 的整体体验如何?",
                "你觉得文档是否清晰易懂?",
                "你希望添加什么新功能?",
            ]
            answers = {}

            await conv.say(
                "[survey] 欢迎参与 ErisPulse 问卷调查! 回复 '退出' 可随时结束"
            )

            for i, question in enumerate(questions, 1):
                await conv.say(f"[survey/{i}/{len(questions)}] {question}")
                reply = await conv.wait()

                if reply is None:
                    await conv.say("[survey] 对话超时，问卷已终止")
                    break

                text = reply.get_text()
                if text.strip() == "退出":
                    await conv.say("[survey] 已退出问卷，感谢参与!")
                    break

                answers[f"q{i}"] = text
            else:
                await conv.say(
                    f"[survey] 问卷完成! 感谢你的参与!\n共收集 {len(answers)} 条回答"
                )

                user_id = event.get_user_id()
                self.storage.set(f"itest:survey:{user_id}", answers)

            if not conv.is_active:
                return

        @command("it.chat", group="InteractiveTest", help="多轮对话 - 自由聊天")
        async def chat_handler(event):
            conv = event.conversation(timeout=120)
            await conv.say("[chat] 进入自由聊天模式! 回复 '再见' 结束对话 (120秒超时)")

            msg_count = 0
            while conv.is_active:
                reply = await conv.wait()
                if reply is None:
                    await conv.say("[chat] 对话超时，再见!")
                    break

                text = reply.get_text().strip()
                msg_count += 1

                if text in ["再见", "bye", "退出", "exit"]:
                    await conv.say(f"[chat] 再见! 本次对话共 {msg_count} 条消息")
                    break

                await conv.say(f"[chat] ({msg_count}) 你说了: {text}")

    # ----------------------------------------------------------
    # OneBot12 消息构建器命令
    # ----------------------------------------------------------

    def _register_message_builder_commands(self):
        @command("it.send_info", group="InteractiveTest", help="查询平台支持的发送方法")
        async def send_info_handler(event):
            platform = event.get_platform()
            adapter = self.sdk.adapter.get(platform)
            if not adapter:
                await event.reply(f"[send_info] 未找到 {platform} 适配器")
                return

            methods = self.sdk.adapter.list_sends(platform)
            if methods:
                method_list = "\n".join(
                    f"  {i + 1}. {m}" for i, m in enumerate(methods)
                )
                await event.reply(
                    f"[send_info] {platform} 平台支持 {len(methods)} 种发送方法:\n{method_list}"
                )
            else:
                await event.reply(f"[send_info] {platform} 平台无可查询的发送方法")

        @command("it.send_detail", group="InteractiveTest", help="查询指定发送方法详情")
        async def send_detail_handler(event):
            args = event.get_command_args()
            if not args:
                await event.reply(
                    "[send_detail] 用法: /it.send_detail <方法名> (如 Text, Image)"
                )
                return

            platform = event.get_platform()
            method_name = args[0]

            info = self.sdk.adapter.send_info(platform, method_name)
            if info:
                params_text = ""
                for p in info.get("parameters", []):
                    default = (
                        f" = {p['default']}" if p.get("default") is not None else ""
                    )
                    params_text += f"\n  - {p['name']}: {p.get('type', '?')}{default}"

                await event.reply(
                    f"[send_detail] {platform}.{method_name}:\n"
                    f"  返回类型: {info.get('return_type', '未知')}\n"
                    f"  文档: {info.get('docstring', '无')}\n"
                    f"  参数:{params_text or '  无参数'}"
                )
            else:
                await event.reply(
                    f"[send_detail] 未找到 {platform}.{method_name} 的信息"
                )

        @command("it.dsl_text", group="InteractiveTest", help="测试 SendDSL 文本发送")
        async def dsl_text_handler(event):
            platform = event.get_platform()
            adapter = self.sdk.adapter.get(platform)
            if not adapter:
                await event.reply("[dsl_text] 未找到适配器")
                return

            user_id = event.get_user_id()
            detail_type = "group" if event.is_group_message() else "user"
            group_id = event.get_group_id()

            if detail_type == "group":
                await adapter.Send.To("group", group_id).Text(
                    "[SendDSL] 这条消息通过 SendDSL 发送到群组"
                )
            else:
                await adapter.Send.To("user", user_id).Text(
                    "[SendDSL] 这条消息通过 SendDSL 发送到私聊"
                )

        @command("it.dsl_at", group="InteractiveTest", help="测试 SendDSL @用户发送")
        async def dsl_at_handler(event):
            platform = event.get_platform()
            adapter = self.sdk.adapter.get(platform)
            if not adapter:
                await event.reply("[dsl_at] 未找到适配器")
                return

            if not event.is_group_message():
                await event.reply("[dsl_at] 此命令仅限群聊使用")
                return

            group_id = event.get_group_id()
            user_id = event.get_user_id()

            await (
                adapter.Send.To("group", group_id)
                .At(user_id)
                .Text("[SendDSL] 你被 @ 了! (通过 SendDSL.At + Text)")
            )

        @command("it.dsl_atall", group="InteractiveTest", help="测试 SendDSL @全体成员")
        async def dsl_atall_handler(event):
            platform = event.get_platform()
            adapter = self.sdk.adapter.get(platform)
            if not adapter:
                await event.reply("[dsl_atall] 未找到适配器")
                return

            if not event.is_group_message():
                await event.reply("[dsl_atall] 此命令仅限群聊使用")
                return

            group_id = event.get_group_id()
            await (
                adapter.Send.To("group", group_id)
                .AtAll()
                .Text("[SendDSL] 这是一条公告 (@全体成员)")
            )

        @command("it.dsl_reply", group="InteractiveTest", help="测试 SendDSL 回复消息")
        async def dsl_reply_handler(event):
            platform = event.get_platform()
            adapter = self.sdk.adapter.get(platform)
            if not adapter:
                await event.reply("[dsl_reply] 未找到适配器")
                return

            msg_id = event.get_id()
            user_id = event.get_user_id()
            detail_type = "group" if event.is_group_message() else "user"
            target_id = event.get_group_id() if event.is_group_message() else user_id

            await (
                adapter.Send.To(detail_type, target_id)
                .Reply(msg_id)
                .Text("[SendDSL] 这是对你消息的回复 (通过 SendDSL.Reply + Text)")
            )

        @command("it.dsl_image", group="InteractiveTest", help="测试 SendDSL 图片发送")
        async def dsl_image_handler(event):
            platform = event.get_platform()
            adapter = self.sdk.adapter.get(platform)
            if not adapter:
                await event.reply("[dsl_image] 未找到适配器")
                return

            user_id = event.get_user_id()
            detail_type = "group" if event.is_group_message() else "user"
            target_id = event.get_group_id() if event.is_group_message() else user_id

            try:
                await adapter.Send.To(detail_type, target_id).Image(
                    "https://httpbin.org/image/png"
                )
            except Exception as e:
                await event.reply(f"[dsl_image] 图片发送失败: {e}")

        @command(
            "it.dsl_using", group="InteractiveTest", help="测试 SendDSL 指定账号发送"
        )
        async def dsl_using_handler(event):
            platform = event.get_platform()
            adapter = self.sdk.adapter.get(platform)
            if not adapter:
                await event.reply("[dsl_using] 未找到适配器")
                return

            bots = self.sdk.adapter.list_bots()
            platform_bots = bots.get(platform, {})

            if not platform_bots:
                await event.reply(f"[dsl_using] {platform} 平台暂无在线 Bot")
                return

            bot_ids = list(platform_bots.keys())
            user_id = event.get_user_id()

            self.logger.info(f"可用 Bots: {bot_ids}")
            await event.reply(
                f"[dsl_using] {platform} 平台当前有 {len(bot_ids)} 个 Bot:\n"
                + "\n".join(f"  - {bid}" for bid in bot_ids)
            )

        @command(
            "it.dsl_multi", group="InteractiveTest", help="测试 SendDSL 组合消息发送"
        )
        async def dsl_multi_handler(event):
            platform = event.get_platform()
            adapter = self.sdk.adapter.get(platform)
            if not adapter:
                await event.reply("[dsl_multi] 未找到适配器")
                return

            if not event.is_group_message():
                await event.reply("[dsl_multi] 此命令仅限群聊使用 (需要 @ 功能)")
                return

            group_id = event.get_group_id()
            user_id = event.get_user_id()
            msg_id = event.get_id()

            await (
                adapter.Send.To("group", group_id)
                .At(user_id)
                .Reply(msg_id)
                .Text("[SendDSL] 组合消息: @你 + 回复你的消息 + 文本内容")
            )

        @command(
            "it.reply_methods",
            group="InteractiveTest",
            help="测试 event.reply 各种修饰参数",
        )
        async def reply_methods_handler(event):
            user_id = event.get_user_id()

            await event.reply("[reply] 1. 纯文本回复")

            await asyncio.sleep(0.5)

            if event.is_group_message():
                await event.reply("[reply] 2. @用户回复", at_users=[user_id])

                await asyncio.sleep(0.5)

                await event.reply("[reply] 3. 回复消息", reply_to=event.get_id())

                await asyncio.sleep(0.5)

                await event.reply(
                    "[reply] 4. @用户 + 回复消息",
                    at_users=[user_id],
                    reply_to=event.get_id(),
                )
            else:
                await event.reply("[reply] 2-4 需要群聊环境 (@/回复)")

            await asyncio.sleep(0.5)

            try:
                await event.reply("https://httpbin.org/image/png", method="Image")
            except Exception as e:
                await event.reply(f"[reply] 5. 图片发送失败: {e}")

    # ----------------------------------------------------------
    # 事件信息命令
    # ----------------------------------------------------------

    def _register_event_info_commands(self):
        @command("it.event_info", group="InteractiveTest", help="查看完整事件信息")
        async def event_info_handler(event):
            info = (
                f"[event_info] 事件详情:\n"
                f"  事件ID: {event.get_id()}\n"
                f"  时间戳: {event.get_time()}\n"
                f"  事件类型: {event.get_type()}\n"
                f"  详细类型: {event.get_detail_type()}\n"
                f"  平台: {event.get_platform()}\n"
                f"  机器人ID: {event.get_self_user_id()}\n"
                f"  机器人平台: {event.get_self_platform()}\n"
                f"  用户ID: {event.get_user_id()}\n"
                f"  用户昵称: {event.get_user_nickname()}\n"
                f"  纯文本: {event.get_text()}\n"
                f"  消息段数: {len(event.get_message())}\n"
                f"  是否私聊: {event.is_private_message()}\n"
                f"  是否群聊: {event.is_group_message()}\n"
                f"  是否@: {event.is_at_message()}\n"
                f"  是否命令: {event.is_command()}"
            )

            if event.is_group_message():
                info += f"\n  群组ID: {event.get_group_id()}"

            if event.is_at_message():
                mentions = event.get_mentions()
                info += f"\n  @用户列表: {mentions}"

            if event.is_command():
                info += (
                    f"\n  命令名: {event.get_command_name()}\n"
                    f"  命令参数: {event.get_command_args()}\n"
                    f"  命令原文: {event.get_command_raw()}"
                )

            has_mentions = event.has_mention()
            info += f"\n  @了机器人: {has_mentions}"

            raw = event.get_raw()
            raw_type = event.get_raw_type()
            info += f"\n  原始数据类型: {raw_type}"

            await event.reply(info)

        @command(
            "it.platform_methods",
            group="InteractiveTest",
            help="查看平台注册的扩展方法",
        )
        async def platform_methods_handler(event):
            from ErisPulse.Core.Event import get_platform_event_methods

            platform = event.get_platform()
            methods = get_platform_event_methods(platform)

            if methods:
                method_list = "\n".join(f"  - {m}" for m in methods)
                await event.reply(
                    f"[platform_methods] {platform} 注册了 {len(methods)} 个扩展方法:\n{method_list}"
                )
            else:
                await event.reply(f"[platform_methods] {platform} 未注册扩展方法")

            all_attrs = dir(event)
            custom_attrs = [
                a
                for a in all_attrs
                if a.startswith("get_")
                and a
                not in {
                    "get_id",
                    "get_time",
                    "get_type",
                    "get_detail_type",
                    "get_platform",
                    "get_self_platform",
                    "get_self_user_id",
                    "get_self_info",
                    "get_message",
                    "get_alt_message",
                    "get_text",
                    "get_message_text",
                    "get_user_id",
                    "get_user_nickname",
                    "get_sender",
                    "get_group_id",
                    "get_channel_id",
                    "get_guild_id",
                    "get_thread_id",
                    "get_mentions",
                    "get_operator_id",
                    "get_operator_nickname",
                    "get_comment",
                    "get_raw",
                    "get_raw_type",
                    "get_command_name",
                    "get_command_args",
                    "get_command_raw",
                    "get_command_info",
                }
            ]
            if custom_attrs:
                await event.reply(
                    f"[platform_methods] {platform} 专有属性:\n"
                    + "\n".join(f"  - {a}" for a in custom_attrs)
                )

        @command("it.bot_status", group="InteractiveTest", help="查看所有 Bot 在线状态")
        async def bot_status_handler(event):
            bots = self.sdk.adapter.list_bots()
            if not bots:
                await event.reply("[bot_status] 当前无在线 Bot")
                return

            lines = []
            for platform_name, bot_list in bots.items():
                lines.append(f"[{platform_name}]")
                for bot_id, info in bot_list.items():
                    status = info.get("status", "unknown")
                    lines.append(f"  {bot_id}: {status}")

            summary = self.sdk.adapter.get_status_summary()
            lines.append(f"\n状态摘要: {summary}")

            await event.reply("[bot_status] Bot 状态:\n" + "\n".join(lines))

    # ----------------------------------------------------------
    # 存储系统命令
    # ----------------------------------------------------------

    def _register_storage_commands(self):
        @command(
            "it.storage_set",
            group="InteractiveTest",
            help="测试存储写入 (it.storage_set <key> <value>)",
        )
        async def storage_set_handler(event):
            args = event.get_command_args()
            if len(args) < 2:
                await event.reply("[storage_set] 用法: /it.storage_set <key> <value>")
                return

            key = f"itest:{args[0]}"
            value = " ".join(args[1:])
            self.storage.set(key, value)
            await event.reply(f"[storage_set] 已写入: {key} = {value}")

        @command(
            "it.storage_get",
            group="InteractiveTest",
            help="测试存储读取 (it.storage_get <key>)",
        )
        async def storage_get_handler(event):
            args = event.get_command_args()
            if not args:
                await event.reply("[storage_get] 用法: /it.storage_get <key>")
                return

            key = f"itest:{args[0]}"
            value = self.storage.get(key)
            if value is not None:
                await event.reply(f"[storage_get] {key} = {value}")
            else:
                await event.reply(f"[storage_get] 键 {key} 不存在")

        @command(
            "it.storage_delete",
            group="InteractiveTest",
            help="测试存储删除 (it.storage_delete <key>)",
        )
        async def storage_delete_handler(event):
            args = event.get_command_args()
            if not args:
                await event.reply("[storage_delete] 用法: /it.storage_delete <key>")
                return

            key = f"itest:{args[0]}"
            self.storage.delete(key)
            await event.reply(f"[storage_delete] 已删除: {key}")

        @command(
            "it.storage_transaction", group="InteractiveTest", help="测试事务批量写入"
        )
        async def storage_transaction_handler(event):
            try:
                with self.storage.transaction():
                    self.storage.set("itest:tx:a", "value_a")
                    self.storage.set("itest:tx:b", "value_b")
                    self.storage.set("itest:tx:c", "value_c")
                a = self.storage.get("itest:tx:a")
                b = self.storage.get("itest:tx:b")
                c = self.storage.get("itest:tx:c")
                await event.reply(
                    f"[storage_transaction] 事务提交成功!\n"
                    f"  a = {a}\n  b = {b}\n  c = {c}"
                )
            except Exception as e:
                await event.reply(f"[storage_transaction] 事务失败: {e}")

        @command("it.storage_multi", group="InteractiveTest", help="测试批量写入")
        async def storage_multi_handler(event):
            self.storage.set_multi(
                {
                    "itest:multi:1": "one",
                    "itest:multi:2": "two",
                    "itest:multi:3": "three",
                }
            )
            await event.reply("[storage_multi] 批量写入完成 (itest:multi:1/2/3)")

    # ============================================================
    # 消息事件处理器
    # ============================================================

    def _register_message_handlers(self):
        @message.on_message(priority=100)
        async def message_logger(event):
            user_id = event.get_user_id()
            platform = event.get_platform()
            text = event.get_text()
            is_cmd = event.is_command()
            group_id = event.get_group_id() if event.is_group_message() else None

            location = f"群:{group_id}" if group_id else "私聊"
            self.logger.info(
                f"[消息日志] {platform}/{location} {user_id}: "
                f"{'[CMD] ' if is_cmd else ''}{text[:80]}"
            )

    # ============================================================
    # 通知事件处理器
    # ============================================================

    def _register_notice_handlers(self):
        @notice.on_friend_add()
        async def friend_add_handler(event):
            user_id = event.get_user_id()
            nickname = event.get_user_nickname() or "新朋友"
            self.logger.info(f"[通知] 新好友: {nickname} ({user_id})")
            await event.reply(f"[InteractiveTest] 欢迎 {nickname}! 我是测试机器人。")

        @notice.on_group_increase()
        async def group_increase_handler(event):
            user_id = event.get_user_id()
            group_id = event.get_group_id()
            self.logger.info(f"[通知] 群 {group_id} 新成员: {user_id}")

    # ============================================================
    # 元事件处理器
    # ============================================================

    def _register_meta_handlers(self):
        @meta.on_connect()
        async def connect_handler(event):
            platform = event.get_platform()
            self.logger.info(f"[元事件] {platform} 已连接")

        @meta.on_disconnect()
        async def disconnect_handler(event):
            platform = event.get_platform()
            self.logger.warning(f"[元事件] {platform} 已断开")
