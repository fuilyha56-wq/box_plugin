"""Box Plugin 通用工具。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import httpx

from src.app.plugin_system.api.log_api import get_logger

logger = get_logger("box_plugin.utils")


async def get_avatar(user_id: str, *, timeout: float = 10.0) -> bytes | None:
    """下载用户 QQ 头像。

    Args:
        user_id: 目标用户 QQ 号
        timeout: HTTP 超时秒数

    Returns:
        头像字节流，失败时返回 None
    """
    avatar_url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(avatar_url)
            response.raise_for_status()
            return response.content
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"下载头像失败 user_id={user_id}: {exc}")
        return None


async def download_file(
    url: str,
    target_path: Path,
    *,
    timeout: float = 30.0,
) -> bool:
    """下载远程文件到目标路径。

    Args:
        url: 远程文件 URL
        target_path: 目标本地路径
        timeout: HTTP 超时秒数

    Returns:
        是否下载成功
    """
    if not url:
        return False

    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.with_suffix(target_path.suffix + ".part")

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with tmp_path.open("wb") as fp:
                    async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                        if chunk:
                            fp.write(chunk)
        tmp_path.replace(target_path)
        logger.info(f"已下载文件到 {target_path}")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"下载文件失败 url={url}: {exc}")
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        return False


def render_digest(display: list[str], avatar: bytes | None) -> str:
    """根据显示内容与头像计算缓存摘要。"""
    payload = {
        "display": display,
        "avatar": hashlib.md5(avatar).hexdigest() if avatar else "",
    }
    return hashlib.md5(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def filter_protected_users(
    target_ids: list[str],
    protect_ids: list[str],
    self_id: str = "",
) -> list[str]:
    """过滤掉受保护用户，返回剩余的可开盒列表。"""
    protected: set[str] = {str(pid) for pid in protect_ids}
    if self_id:
        protected.add(str(self_id))
    return [tid for tid in target_ids if str(tid) not in protected]
