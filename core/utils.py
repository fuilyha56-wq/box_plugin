import hashlib
import json
import aiohttp
from src.common.logger import get_logger
from typing import List, Optional, Set

logger = get_logger("box_plugin.utils")

async def get_avatar(user_id: str) -> Optional[bytes]:
    """获取用户头像"""
    avatar_url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as response:
                response.raise_for_status()
                return await response.read()
    except Exception as e:
        logger.error(f"下载头像失败: {e}")
        return None


def get_ats_from_message(message_segments: List[dict], exclude_self: bool = False, self_id: str = "") -> List[str]:
    """从消息中提取被@的用户ID列表"""
    ats = []
    for segment in message_segments:
        if segment.get("type") == "at":
            qq = segment.get("data", {}).get("qq")
            if qq:
                # 如果需要排除自己且QQ号是自己的，则跳过
                if exclude_self and qq == self_id:
                    continue
                ats.append(str(qq))
    return ats


def render_digest(display: list, avatar: bytes) -> str:
    """计算哈希值：全字段(int/str)保留，头像单独md5"""
    payload = {
        "display": display,
        "avatar": hashlib.md5(avatar).hexdigest() if avatar else "",
    }
    return hashlib.md5(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def filter_protected_users(target_ids: List[str], protect_ids: List[str], self_id: str = "") -> List[str]:
    """过滤受保护的用户"""
    protected_set: Set[str] = set(protect_ids)
    if self_id:
        protected_set.add(self_id)
    
    # 过滤掉受保护的用户
    filtered_ids = [tid for tid in target_ids if tid not in protected_set]
    return filtered_ids