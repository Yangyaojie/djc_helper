# 构建发布压缩包
import os
import re
import shutil
import subprocess

from log import logger
from version import now_version


def package(dir_src, dir_all_release, release_dir_name, release_7z_name, dir_github_action_artifact):
    old_cwd = os.getcwd()

    # 需要复制的文件与目录
    files_to_copy = []
    reg_wantted_file = r'.*\.(toml|md|txt|png|jpg|docx|url)$'
    for file in os.listdir('.'):
        if not re.search(reg_wantted_file, file, flags=re.IGNORECASE):
            continue
        files_to_copy.append(file)
    files_to_copy.extend([
        "config.toml.example",
        "DNF蚊子腿小助手.exe",
        "DNF蚊子腿小助手配置工具.exe",
        "双击打开配置文件.bat",
        "清除登录信息_误登录其他账号后请点击这个.bat",
        "bandizip_portable",
        "reference_data",
        "chromedriver_87.exe",
        "public_key.der",
        "使用教程",
        "npp_portable",
        "utils",
        "icons",
    ])
    files_to_copy = sorted(files_to_copy)

    # 确保发布根目录存在
    if not os.path.isdir(dir_all_release):
        os.mkdir(dir_all_release)
    # 并清空当前的发布版本目录
    dir_current_release = os.path.realpath(os.path.join(dir_all_release, release_dir_name))
    shutil.rmtree(dir_current_release, ignore_errors=True)
    os.mkdir(dir_current_release)
    # 复制文件与目录过去
    logger.info(f"将以下内容从{dir_src}复制到{dir_current_release}")
    for filename in files_to_copy:
        source = os.path.join(dir_src, filename)
        destination = os.path.join(dir_current_release, filename)
        if os.path.isdir(filename):
            logger.info(f"拷贝目录 {filename}")
            shutil.copytree(source, destination)
        else:
            logger.info(f"拷贝文件 {filename}")
            shutil.copyfile(source, destination)

    logger.info("清除utils目录下的一些内容")
    for filename in ["logs", ".db", "auto_updater.exe", "buy_auto_updater_users.txt"]:
        filepath = os.path.join(dir_current_release, f"utils/{filename}")
        if not os.path.exists(filepath):
            continue

        if os.path.isdir(filepath):
            logger.info(f"移除目录 {filepath}")
            shutil.rmtree(filepath, ignore_errors=True)
        else:
            logger.info(f"移除文件 {filepath}")
            os.remove(filepath)

    # 压缩打包
    os.chdir(dir_all_release)
    logger.info("开始压缩打包")
    path_bz = os.path.join(dir_src, "bandizip_portable", "bz.exe")
    subprocess.call([path_bz, 'c', '-y', '-r', '-aoa', '-fmt:7z', '-l:9', release_7z_name, release_dir_name])

    # 额外备份一份最新的供github action 使用
    shutil.copyfile(release_7z_name, os.path.join(dir_github_action_artifact, 'djc_helper.7z'))

    os.chdir(old_cwd)


def main():
    dir_src = os.path.realpath('.')
    dir_all_release = os.path.realpath(os.path.join("releases"))
    release_dir_name = f"DNF蚊子腿小助手_v{now_version}_by风之凌殇"
    release_7z_name = f'{release_dir_name}.7z'
    dir_github_action_artifact = "_github_action_artifact"

    package(dir_src, dir_all_release, release_dir_name, release_7z_name, dir_github_action_artifact)


if __name__ == '__main__':
    main()
