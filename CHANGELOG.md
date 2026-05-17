# 开盒插件更新日志

## [2.0.0] - 2026-05-17

### 修复
- 修复可爱字体下载 URL 失效（上游仓库默认分支变更：`master/font/` → `main/core/resource/`）
- 字体下载新增**已知失效 URL 自动迁移**机制：检测到旧 URL 时自动改用最新默认地址
- 字体下载新增**主 URL 失败自动回退到默认 URL**的兜底逻辑
- 修复 QQ 等级 emoji（皇冠/太阳/月亮/星星）无法显示的问题：
  - `NotoColorEmoji.ttf` 是 CBDT 位图字体，必须用 strike 尺寸 109 加载，并启用 `embedded_color=True`
  - emoji 在独立画布渲染后裁剪缩放贴回，行高更稳定

### 新增
- 多字体路由：按字符 cmap 自动选择 `cute → cjk_kr → latin` 字体
- 新增 **NotoSans Regular** fallback（825 KB）：覆盖**俄语 / 希腊 / 拉丁扩展**等可爱字体未覆盖的字符
- 新增 **NotoSansKR Regular** fallback（4.5 MB）：覆盖**韩语昵称、日语片假名**等
- 新增 `latin_font_url` / `cjk_kr_font_url` 两项配置，可自定义下载地址
- 运行时新增 `fonttools` 依赖，用于精确读取字体 cmap

### 重大变更
- 全面适配 **Neo-MoFox** 插件系统规范（`src.app.plugin_system` 公共入口）
- 许可证从 AGPL 改为 **GPL-3.0**，与 context_bridge_tool 保持一致
- 作者署名更新为 **Lycoris&ikun**

### 新增
- 新增 [`manifest.json`](manifest.json:1)，按规范声明组件类型 / 签名 / Python 依赖
- 新增 [`config.py`](config.py:1)：使用 `BaseConfig + SectionBase + @config_section` 定义结构化配置
- 新增 [`config.example.toml`](config.example.toml:1)：与配置类同步的示例文件
- 字体首次运行**自动从远端下载**到 `data/fonts/`，发布包不再随附 4MB 字体
- 新增 `[adapter]` 配置：可自定义 Adapter 签名与 API 超时
- 新增 `[font]` 配置：可自定义中文 / Emoji 字体下载 URL 与超时
- `BoxCommand` 使用 `BaseCommand` + `@cmd_route` + `match()` 同时匹配 “盒” 与 “开盒”
- `GroupMemberHandler` 使用 `BaseEventHandler`，订阅 `ON_NOTICE_RECEIVED`，返回 `EventDecision`
- 引入 `httpx` 取代 `aiohttp`，并加入 `requirements.txt`

### 修改
- 用 `adapter_api.send_adapter_command` 替换旧的 `send_api.adapter_command_to_stream`
- 所有日志改用 `src.app.plugin_system.api.log_api.get_logger`
- 全部插件内部模块改用**相对导入**（`from ..config import ...`）
- `CardMaker` 接受外部传入字体路径，并在文件不存在时回退到 PIL 默认字体

### 移除
- 移除 `core/resource/` 下的字体文件（约 3.7MB）
- 移除旧的 `tests/`、`docs/`（与新结构不再兼容）
- 移除旧的 `__init__.py` 中 `PluginMetadata` 风格元数据，统一由 `manifest.json` 提供

## [1.2.0] - 2026-01-07

### 修复
- 修复 @ 别人开盒显示自己身份的问题
- 修复 `@<昵称:QQ号>` 格式解析问题
- 自动将 Bot 加入保护名单

## [1.1.0] - 2026-01-07

### 修改
- 重构显示选项配置格式，使用英文键名独立的 true/false 配置项

## [1.0.0] - 2026-01-06

### 新增
- 实现基本开盒功能，支持 `/盒` 与 `/开盒`
- 实现开盒卡片图片生成、缓存机制、撤回功能与保护名单
