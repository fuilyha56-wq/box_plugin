import asyncio
import weakref
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from src.common.logger import get_logger
from .draw import CardMaker
from .field_mapping import FIELD_MAPPING, LABEL_TO_KEY, ALL_LABELS, LABEL_TO_CONFIG_KEY
from .utils import get_avatar, render_digest

logger = get_logger("box_plugin.core")

class BoxCore:
    """开盒核心逻辑"""
    
    def __init__(self, plugin_dir: str, config_getter):
        self.get_config = config_getter
        
        # 缓存目录
        self.cache_dir: Path = Path(plugin_dir) / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 卡片生成器
        resource_dir = Path(__file__).parent / "resource"
        self.renderer = CardMaker(resource_dir)
        
        # 撤回任务
        self._recall_tasks: weakref.WeakSet[asyncio.Task] = weakref.WeakSet()
        
    async def box_user(self, target_id: str, group_id: str, sender_id: str, is_admin: bool = False) -> Optional[bytes]:
        """开盒用户"""
        try:
            # 检查权限
            only_admin = self.get_config("basic.only_admin", False)
            if only_admin and not is_admin and target_id != sender_id:
                logger.info("非管理员尝试开盒他人，已被阻止")
                return None
                
            # 检查保护名单
            protect_ids = self.get_config("protection.protect_ids", [])
            if target_id in protect_ids and target_id != sender_id:
                logger.info(f"用户 {target_id} 在保护名单中，无法开盒")
                return None
                
            # 获取用户信息（这里需要适配MoFox的API）
            user_info = await self._get_user_info(target_id, group_id)
            if not user_info:
                logger.error(f"无法获取用户 {target_id} 的信息")
                return None
                
            # 获取头像
            avatar = await get_avatar(target_id)
            if not avatar:
                # 使用默认头像
                avatar = self._get_default_avatar()
                
            # 解析用户信息
            display = self._transform_user_info(user_info)
            
            # 附加真实信息（如果有的话）
            # TODO: 实现Library客户端功能
            
            # 缓存机制
            digest = render_digest(display, avatar)
            cache_name = f"{target_id}_{group_id}_{digest}.png"
            cache_path = self.cache_dir / cache_name
            
            if cache_path.exists():
                image = cache_path.read_bytes()
                logger.debug(f"命中缓存: {cache_path}")
            else:
                image = self.renderer.create(avatar, display)
                cache_path.write_bytes(image)
                logger.debug(f"写入缓存: {cache_path}")
                
            return image
        except Exception as e:
            logger.error(f"开盒用户 {target_id} 失败: {e}")
            return None
    
    async def _get_user_info(self, user_id: str, group_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息（需要适配MoFox的API）"""
        try:
            from src.plugin_system.apis import send_api
            
            # 获取陌生人信息
            stranger_response = await send_api.adapter_command_to_stream(
                action="get_stranger_info",
                params={"user_id": int(user_id)},
                timeout=30.0
            )
            
            stranger_info = {}
            if stranger_response.get("status") == "ok":
                stranger_info = stranger_response.get("data", {})
            
            # 获取群成员信息（如果在群聊中）
            member_info = {}
            if group_id:
                try:
                    member_response = await send_api.adapter_command_to_stream(
                        action="get_group_member_info",
                        params={"group_id": int(group_id), "user_id": int(user_id)},
                        timeout=30.0
                    )
                    
                    if member_response.get("status") == "ok":
                        member_info = member_response.get("data", {})
                except Exception as e:
                    logger.warning(f"获取群成员信息失败: {e}")
            
            user_info = {
                "stranger_info": stranger_info,
                "member_info": member_info
            }
            
            return user_info
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None
    
    def _transform_user_info(self, user_info: Dict[str, Any]) -> List[str]:
        """根据映射表转换用户信息为显示列表"""
        reply: List[str] = []
        
        stranger_info = user_info.get("stranger_info", {})
        member_info = user_info.get("member_info", {})
        
        # 获取所有显示选项的配置，根据true/false值决定是否显示
        enabled_keys = set()
        for label in ALL_LABELS:
            # 获取配置键名
            config_key = LABEL_TO_CONFIG_KEY.get(label, label)
            # 获取配置值，默认为True（保持向后兼容）
            is_enabled = self.get_config(f"display.{config_key}", True)
            if is_enabled:
                # 将启用的中文标签转换为英文字段名
                key = LABEL_TO_KEY.get(label, label)
                enabled_keys.add(key)

        for field in FIELD_MAPPING:
            key = field["key"]
            label = field["label"]
            source = field.get("source", "info1")

            # 检查是否启用显示
            if key not in enabled_keys:
                continue

            # 处理计算字段
            if source == "computed":
                computed_lines = self._compute_field(key, label, stranger_info, member_info)
                if computed_lines:
                    reply.extend(computed_lines)
                continue

            # 获取原始值
            data = stranger_info if source == "info1" else member_info
            value = data.get(key)

            # 跳过空值
            if not value:
                continue

            # 跳过特定值
            skip_values = field.get("skip_values", [])
            if value in skip_values:
                continue

            # 应用转换函数
            transform = field.get("transform")
            if transform:
                value = transform(value)
                if not value:  # 转换后为空则跳过
                    continue

            # 添加后缀
            suffix = field.get("suffix", "")

            # 处理多行文本（如签名）
            if field.get("multiline"):
                import textwrap
                wrap_width = field.get("wrap_width", 15)
                lines = textwrap.wrap(text=f"{label}：{value}", width=wrap_width)
                reply.extend(lines)
            else:
                reply.append(f"{label}：{value}{suffix}")

        return reply
    
    def _compute_field(self, key: str, label: str, info1: dict, info2: dict) -> list[str]:
        """处理需要特殊计算的字段，返回行列表"""
        
        if key == "birthday":
            year = info1.get("birthday_year")
            month = info1.get("birthday_month")
            day = info1.get("birthday_day")
            if year and month and day:
                return [f"{label}：{year}-{month}-{day}"]
            return []

        if key == "constellation":
            month = info1.get("birthday_month")
            day = info1.get("birthday_day")
            if month and day:
                from .field_mapping import get_constellation
                return [f"{label}：{get_constellation(int(month), int(day))}"]
            return []

        if key == "zodiac":
            year = info1.get("birthday_year")
            month = info1.get("birthday_month")
            day = info1.get("birthday_day")
            if year and month and day:
                from .field_mapping import get_zodiac
                return [f"{label}：{get_zodiac(int(year), int(month), int(day))}"]
            return []

        if key == "address":
            country = info1.get("country")
            province = info1.get("province")
            city = info1.get("city")

            if country == "中国" and (province or city):
                return [f"{label}：{province or ''}-{city or ''}"]
            elif country:
                return [f"{label}：{country}"]
            return []

        if key == "detail_address":
            address = info1.get("address")
            if address and address != "-":
                return [f"{label}：{address}"]
            return []

        return []
    
    def _get_default_avatar(self) -> bytes:
        """获取默认头像"""
        # 创建一个默认的白色头像
        from PIL import Image
        from io import BytesIO
        
        img = Image.new("RGB", (640, 640), (255, 255, 255))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    
    async def cleanup(self):
        """清理资源"""
        # 取消未完成的撤回任务
        if self._recall_tasks:
            for t in list(self._recall_tasks):
                t.cancel()
            await asyncio.gather(*self._recall_tasks, return_exceptions=True)

        # 清空缓存目录
        clean_cache = self.get_config("basic.clean_cache", False)
        if clean_cache and self.cache_dir and self.cache_dir.exists():
            try:
                shutil.rmtree(self.cache_dir)
                logger.debug(f"[BoxCore] 缓存已清空：{self.cache_dir}")
            except Exception as e:
                logger.error(f"[BoxCore] 清空缓存失败：{e}")
            self.cache_dir.mkdir(parents=True, exist_ok=True)