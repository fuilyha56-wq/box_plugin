# 开盒插件 Box Plugin

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

适用于 **Neo-MoFox** 的开盒插件：通过 OneBot 协议获取 QQ 用户信息，并以图片卡片形式展示。

## 功能特性

- 通过 `/盒` 或 `/开盒` 命令开盒指定用户
- 支持 `@用户` 与纯 QQ 号两种目标格式
- 入群 / 退群事件自动开盒（可按群白名单启用）
- 支持 26+ 个字段（昵称、群头衔、生日、星座、生肖、QQ 等级、签名……）独立显示开关
- 可配置 Bot 管理员限制、保护名单、缓存清理
- 支持自定义 Adapter 签名，默认对接 `napcat_adapter`
- 字体资源**首次运行自动下载**，发布包内不再随附 4MB 字体文件

## 安装

1. 将整个 `box_plugin/` 目录放入 Neo-MoFox 的 `plugins/` 下
2. 启动 Neo-MoFox，插件首次加载时会自动：
   - 生成 `config/plugins/box_plugin/config.toml`
   - 下载所需字体到 `plugins/box_plugin/data/fonts/`
3. 按需修改 `config.toml`

## 命令用法

| 命令 | 说明 |
| --- | --- |
| `/盒` | 私聊：开盒自己；群聊：提示需要 @ 用户 |
| `/盒 @某人` | 开盒被 @ 的用户 |
| `/盒 <QQ号>` | 按 QQ 号开盒 |
| `/开盒 ...` | `/盒` 的中文别名，参数相同 |

## 配置说明

参见 [`config.example.toml`](config.example.toml:1)，主要分节：

- `[plugin]` 启用开关与版本信息
- `[basic]` 基础行为（管理员限制、缓存清理）
- `[groups]` 自动开盒群白名单
- `[protection]` 保护用户名单
- `[display]` 26+ 字段显示开关
- `[recall]` 撤回时间（暂作日志占位）
- `[adapter]` 适配器签名与 API 超时
- `[font]` 字体下载 URL、超时、是否跳过 Emoji 字体

## 字体资源

为了大幅减小发布包体积（从约 4MB 降至 <50KB），中文字体与 Emoji 字体不再随插件分发。
插件首次加载时会按 `[font]` 配置的 URL 下载到 `plugins/box_plugin/data/fonts/`。
若下载失败，将自动回退到 PIL 默认字体（仍可生成卡片，但字形可能较朴素）。

## 依赖

- Pillow ≥ 9.0.0
- emoji ≥ 2.0.0
- zhdate ≥ 0.1.0
- httpx ≥ 0.24.0

## 注意事项

1. 本插件依赖 OneBot v11 协议适配器（默认对接 `napcat_adapter`）。
2. 部分字段（电话/邮箱等）可能因隐私设置无法获取，已默认关闭。
3. 请合理使用，尊重他人隐私。

## 版权信息

- 原作者：Zhalslar（[astrbot_plugin_box](https://github.com/Zhalslar/astrbot_plugin_box)）
- 移植与重构：**Lycoris&ikun**
- 许可证：**GPL-3.0**（与项目 [`LICENSE`](LICENSE:1) 一致）
