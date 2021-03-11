import platform
import random
import re
import webbrowser
from datetime import datetime

import requests
import win32api
import win32con

from config import CommonConfig
from dao import UpdateInfo
from log import logger, color
from upload_lanzouyun import Uploader, lanzou_cookie
from util import is_first_run, use_by_myself, async_call
from version import now_version, ver_time


def get_update_desc(config: CommonConfig):
    try:
        uploader = Uploader(lanzou_cookie)
        latest_version = uploader.latest_version()

        if not need_update(now_version, latest_version):
            return ""

        return f"最新版本为v{latest_version}，请及时更新~"
    except Exception as e:
        logger.debug("get_update_desc error", exc_info=e)
        return ""


# 启动时检查是否有更新
def check_update_on_start(config: CommonConfig):
    try:
        if not config.check_update_on_start and not config.auto_update_on_start:
            logger.warning("启动时检查更新被禁用，若需启用请在config.toml中设置")
            return

        ui = get_update_info(config)

        if config.check_update_on_start:
            try_manaual_update(ui)

        if config.auto_update_on_start:
            show_update_info_on_first_run(ui)
    except Exception as err:
        logger.error(
            f"检查版本更新失败（这个跟自动更新没有任何关系）,大概率是访问不了github导致的，可自行前往网盘查看是否有更新, 错误为{err}"
            + color("bold_green") + f"\n（无法理解上面这段话的话，就当没看见这段话，对正常功能没有任何影响）"
        )

        # 如果一直连不上github，则尝试判断距离上次更新的时间是否已经很长
        time_since_last_update = datetime.now() - datetime.strptime(ver_time, "%Y-%m-%d")
        if time_since_last_update.days >= 7:
            msg = f"无法访问github确认是否有新版本，而当前版本更新于{ver_time}，距今已有{time_since_last_update}，很可能已经有新的版本，建议打开目录中的[网盘链接]看看是否有新版本，或者购买自动更新DLC省去手动更新的操作"
            logger.info(color("bold_green") + msg)
            if is_first_run(f"notify_manual_update_if_can_not_connect_github_v{now_version}"):
                win32api.MessageBox(0, msg, "更新提示", win32con.MB_ICONINFORMATION)
                webbrowser.open("https://fzls.lanzous.com/s/djc-helper")


def try_manaual_update(ui: UpdateInfo) -> bool:
    if need_update(now_version, ui.latest_version):
        logger.info(f"当前版本为{now_version}，已有最新版本{ui.latest_version}，更新内容为{ui.update_message}")

        ask_update = True
        if platform.system() == "Windows":
            message = (
                f"当前版本为{now_version}，已有最新版本{ui.latest_version}. 你需要更新吗?\n"
                f"{ui.update_message}"
            )
            res = win32api.MessageBox(0, message, "更新", win32con.MB_OKCANCEL)
            if res == win32con.IDOK:
                ask_update = True
            else:
                ask_update = False
        else:
            # 非windows系统默认更新
            ask_update = True

        if ask_update:
            if not is_shared_content_blocked(ui.netdisk_link):
                webbrowser.open(ui.netdisk_link)
                win32api.MessageBox(0, f"蓝奏云网盘提取码为： {ui.netdisk_passcode}", "蓝奏云网盘提取码", win32con.MB_ICONINFORMATION)
            else:
                # 如果分享的网盘链接被系统屏蔽了，写日志并弹窗提示
                logger.warning(f"网盘链接={ui.netdisk_link}又被系统干掉了=-=")
                webbrowser.open("https://github.com/fzls/djc_helper/releases")
                message = (
                    "分享的网盘地址好像又被系统给抽掉了呢=。=先暂时使用github的release页面下载吧0-0\n"
                    "请稍作等待~ 风之凌殇看到这个报错后会尽快更新网盘链接的呢\n"
                    "届时再启动程序将自动获取到最新的网盘地址呢~"
                )
                win32api.MessageBox(0, message, "不好啦", win32con.MB_ICONERROR)
        else:
            message = "如果想停留在当前版本，不想每次启动都弹出前面这个提醒更新的框框，可以前往config.toml，将check_update_on_start的值设为false即可"
            win32api.MessageBox(0, message, "取消启动时自动检查更新方法", win32con.MB_ICONINFORMATION)
    else:
        logger.info(f"当前版本{now_version}已是最新版本，无需更新")

    has_new_version = need_update(now_version, ui.latest_version)
    return has_new_version


def show_update_info_on_first_run(ui: UpdateInfo):
    if now_version == ui.latest_version and is_first_run(f"update_version_v{ui.latest_version}") and not use_by_myself():
        message = (
            f"新版本v{ui.latest_version}已更新完毕，并成功完成首次运行。本次具体更新内容展示如下，以供参考：\n"
            f"{ui.update_message}"
        )

        def cb():
            win32api.MessageBox(0, message, "更新", win32con.MB_OK)

        async_call(cb)


# 获取最新版本号与下载网盘地址
def get_update_info(config) -> UpdateInfo:
    update_info = UpdateInfo()

    # 获取github本项目的readme页面内容和changelog页面内容
    timeout = 3  # 由于国内网络不太好，加个超时
    changelog_html_text = requests.get(config.changelog_page, timeout=timeout).text
    readme_html_text = requests.get(config.readme_page, timeout=timeout).text

    # 从更新日志中提取所有版本信息
    versions = re.findall("(?<=[vV])[0-9.]+(?=\s+\d+\.\d+\.\d+)", changelog_html_text)
    # 找出其中最新的那个版本号
    update_info.latest_version = version_int_list_to_version(max(version_to_version_int_list(ver) for ver in versions))

    # 从readme中提取最新网盘信息
    netdisk_address_matches = re.findall('链接: <a[\s\S]+?rel="nofollow">(?P<link>.+?)<\/a> 提取码: (?P<passcode>[a-zA-Z0-9]+)', readme_html_text, re.MULTILINE)
    # 先选取首个网盘链接作为默认值
    netdisk_link = netdisk_address_matches[0][0]
    netdisk_passcode = netdisk_address_matches[0][1]
    # 然后随机从仍有效的网盘链接中随机一个作为最终结果
    random.seed(datetime.now())
    random.shuffle(netdisk_address_matches)
    for match in netdisk_address_matches:
        if not is_shared_content_blocked(match[0]):
            update_info.netdisk_link = match[0]
            update_info.netdisk_passcode = match[1]
            break

    # 尝试提取更新信息
    update_message_list_match_groupdict = re.search("(?<=更新公告</h1>)\s*<ol>(?P<update_message_list>(\s|\S)+?)</ol>", changelog_html_text, re.MULTILINE).groupdict()
    if "update_message_list" in update_message_list_match_groupdict:
        update_message_list_str = update_message_list_match_groupdict["update_message_list"]
        update_messages = re.findall("<li>(?P<update_message>.+?)</li>", update_message_list_str, re.MULTILINE)
        update_info.update_message = "\n".join(f"{idx + 1}. {message}" for idx, message in enumerate(update_messages))

    logger.info(f"netdisk_address_matches={netdisk_address_matches}, selected=({update_info.netdisk_link}, {update_info.netdisk_passcode})")

    return update_info


# 是否需要更新
def need_update(current_version, latest_version):
    return version_to_version_int_list(current_version) < version_to_version_int_list(latest_version)


# [3, 2, 2] => 3.2.2
def version_int_list_to_version(version_int_list):
    return '.'.join([str(subv) for subv in version_int_list])


# 3.2.2 => [3, 2, 2]
def version_to_version_int_list(version):
    return [int(subv) for subv in version.split('.')]


# 访问网盘地址，确认分享是否被系统干掉了- -
def is_shared_content_blocked(share_netdisk_addr: str) -> bool:
    # 切换蓝奏云，暂时应该不会被屏蔽了- -
    return False


def get_netdisk_addr(config):
    try:
        ui = get_update_info(config)
        return ui.netdisk_link
    except:
        return "https://fzls.lanzous.com/s/djc-helper"


if __name__ == '__main__':
    from config import load_config, config

    load_config()
    cfg = config()
    check_update_on_start(cfg.common)
