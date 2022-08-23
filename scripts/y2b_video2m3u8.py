import argparse
import logging
import os
import re
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import requests
from opencc import OpenCC
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from video2m3u8 import video2m3u8


def simplify_filename(filepath=''):
    dirname = os.path.dirname(filepath)
    basename = os.path.basename(filepath)
    name = OpenCC('t2s').convert(basename)
    name_parts = os.path.splitext(os.path.basename(name))
    name = re.sub(r'[「『【].+', '', name_parts[0])
    name = name if name else name_parts[0]
    name = f'{name}{name_parts[1]}'
    return os.path.join(dirname, name)


def down_video(url, res, dir) -> Path:
    output_template = os.path.join(dir, '%(title)s.%(ext)s')

    # 指定分辨率 并发3
    cmd = f'yt-dlp -f "bv + ba / b / w" -S "res:{res},+codec:avc:m4a" -o "{output_template}" "{url}" --merge-output-format mp4 -N 3'
    print(f'执行命令：{cmd}')
    code = os.system(cmd)
    if code != 0:
        raise Exception('出错了！')
    filepath = list(Path(dir).glob('*'))[0]
    new_filepath = Path(simplify_filename(str(filepath)))
    return filepath.rename(new_filepath)


def parse_inputs():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='请输入youtube视频地址')
    parser.add_argument('res', help='请输入分辨率。支持的分辨率有：1080p 720p 480p 360p')
    parser.add_argument('--name', help='指定标题', default='')
    args = parser.parse_args()
    return args


def main():
    args = parse_inputs()
    url = args.url
    res = args.res
    name = args.name

    with TemporaryDirectory(prefix='downloads_', dir=os.path.realpath('.')) as tmpdir:
        filepath = down_video(url, res, tmpdir)
        if name.strip():
            filepath = filepath.rename(filepath.with_stem(name))
        if not video2m3u8(str(filepath)):
            raise Exception('视频切片上传m3u8失败')

    script = os.path.join(sys.path[0], 'generate_mv_info.py')
    cmd = f'{sys.executable} "{script}"'
    print(f'执行命令：{cmd}')
    code = os.system(cmd)
    if code != 0:
        raise Exception('出错了。。')


def send_dingtalk_message(message: str):
    try:
        retries = Retry(total=3, allowed_methods=['GET', 'POST', 'PUT', 'HEAD'])
    except TypeError:
        retries = Retry(total=3, method_whitelist=['GET', 'POST', 'PUT', 'HEAD'])
    adapter = HTTPAdapter(pool_connections=15, pool_maxsize=15, max_retries=retries)
    session = requests.Session()
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    resp = session.post('https://api.201992.xyz/tools/dingtalk', data={'message': message}, timeout=20)
    return resp.json()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.exception(e)
        send_dingtalk_message(f'❌【y2b_video2m3u8】出错了：\n{e}')
