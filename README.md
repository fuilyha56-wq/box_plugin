# 开盒插件 (Box Plugin)

一个用于获取QQ用户信息并以图片形式展示的MoFox插件。

## 功能特性

- 获取用户基本信息（QQ号、昵称、备注等）
- 获取用户群信息（群昵称、群头衔、群等级等）
- 获取用户个人资料（性别、年龄、生日、星座等）
- 获取用户联系方式（电话、邮箱等）
- 获取用户地理位置信息（家乡、现居地等）
- 获取用户职业、标签等信息
- 获取用户QQ会员信息（QQVIP、年VIP、VIP等级等）
- 获取用户QQ等级信息
- 获取用户注册时间、加群时间等
- 获取用户签名信息
- 支持自定义显示字段
- 支持自动撤回（可配置）
- 支持保护名单（防止被开盒）

## 安装方法

1. 将整个 `box_plugin` 文件夹复制到 MoFox 的 `plugins` 目录下
2. 重启 MoFox 机器人
3. 插件会自动加载并生成配置文件

## 使用方法

### 命令

- `/盒` - 开盒自己
- `/盒 @某人` - 开盒指定用户
- `/盒 QQ号` - 开盒指定QQ号用户
- `/开盒` - 开盒自己（别名）
- `/开盒 @某人` - 开盒指定用户（别名）
- `/开盒 QQ号` - 开盒指定QQ号用户（别名）


## 配置说明

插件配置文件位于 `config/plugins/box_plugin/config.toml`，支持以下配置项：

### 基础设置
- `only_admin`: 是否仅允许管理员开盒他人
- `clean_cache`: 重载插件时是否清空缓存

### 群组设置
- `auto_box_groups`: 自动开盒群聊白名单

### 保护设置
- `protect_ids`: 信息保护用户列表

### 显示设置
- `qq_number`: 是否显示QQ号
- `nickname`: 是否显示昵称
- `remark`: 是否显示备注
- `group_nickname`: 是否显示群昵称
- `group_title`: 是否显示群头衔
- `gender`: 是否显示性别
- `birthday`: 是否显示生日
- `constellation`: 是否显示星座
- `zodiac`: 是否显示生肖
- `age`: 是否显示年龄
- `blood_type`: 是否显示血型
- `phone`: 是否显示电话
- `email`: 是否显示邮箱
- `hometown`: 是否显示家乡
- `address`: 是否显示现居
- `career`: 是否显示职业
- `tags`: 是否显示个性标签
- `risky_account`: 是否显示风险账号
- `robot_account`: 是否显示机器人账号
- `qq_vip`: 是否显示QQVIP
- `year_vip`: 是否显示年VIP
- `vip_level`: 是否显示VIP等级
- `group_level`: 是否显示群等级
- `join_time`: 是否显示加群时间
- `qq_level`: 是否显示QQ等级
- `reg_time`: 是否显示注册时间
- `signature`: 是否显示签名

### 撤回设置
- `recall_time`: 撤回时间（秒）

## 依赖说明

- Pillow: 图片处理库
- emoji: Emoji处理库
- zhdate: 农历日期处理库

## 注意事项

1. 本插件需要Onebot协议支持才能获取用户信息
2. 部分用户信息可能因隐私设置而无法获取
3. 请合理使用本插件，尊重他人隐私
4. 建议设置保护名单，避免重要用户被开盒

## 版权信息

- 原作者: Zhalslar
- 移植到MoFox: ikun两年半
- 修改来源: https://github.com/Zhalslar/astrbot_plugin_box
- 许可证: AGPL