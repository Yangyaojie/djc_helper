from sys import exit

import win32api
import win32con

from log import logger, color
from util import uin2qq


class BlackListInfo:
    def __init__(self, ban_at, qq, nickname, reason):
        self.ban_at = ban_at
        self.qq = qq
        self.nickname = nickname
        self.reason = reason

    def __str__(self):
        return f"{self.qq}({self.nickname})在{self.ban_at}因[{self.reason}]被本工具拉入黑名单"


black_list = {
    "823985815": BlackListInfo("2021-01-05", "823985815", "章鱼宝宝。", "伸手党，不看提示直接开问"),
    "1531659746": BlackListInfo("2021-01-20", "1531659746", "北望", "别人图氛围说继续发红包时，骂别人网络乞丐，然后被踢后，加我说我是傻逼罢了"),
    "262163207": BlackListInfo("2021-01-31", "262163207", "孤独患者", "说了不要问我疲劳药怎么设置，也看到注释的内容了，还要问，还说我优越感很强。既然合不来，就再见吧。"),
    "69512151": BlackListInfo("2021-02-22", "69512151", "不知道是谁", "做坏事，永久拉黑"),
    "642364310": BlackListInfo("2021-02-22", "642364310", "不知道是谁", "做坏事，永久拉黑"),
    "39752616": BlackListInfo("2021-02-22", "39752616", "不知道是谁", "做坏事，永久拉黑"),
    "4838116": BlackListInfo("2021-04-03", "4838116", "玉簪子", "不可理喻"),
}


def check_in_black_list(uin):
    qq = uin2qq(uin)
    if qq in black_list:
        message = (
            "发现你的QQ在本工具的黑名单里，本工具禁止你使用，将在本窗口消失后退出运行。\n"
            "黑名单相关信息如下：\n"
            f"{black_list[qq]}"
        )
        logger.warning(color("fg_bold_cyan") + message)
        win32api.MessageBox(0, message, "禁止使用", win32con.MB_OK)
        exit(0)


if __name__ == '__main__':
    check_in_black_list("o823985815")
