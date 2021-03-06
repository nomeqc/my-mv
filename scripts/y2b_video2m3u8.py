import argparse
import os
import re
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from opencc import OpenCC


from video2m3u8 import video2m3u8, precheck


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
    args = parser.parse_args()
    return args


def main():
    args = parse_inputs()
    url = args.url
    res = args.res
    if not precheck():
        return
    with TemporaryDirectory(prefix='downloads_', dir=os.path.realpath('.')) as tmpdir:
        filepath = down_video(url, res, tmpdir)
        if not video2m3u8(str(filepath)):
            raise Exception('视频切片上传m3u8失败')
    script = os.path.join(sys.path[0], 'generate_mv_info.py')
    cmd = f'{sys.executable} "{script}"'
    print(f'执行命令：{cmd}')
    code = os.system(cmd)
    if code != 0:
        raise Exception('出错了。。')


if __name__ == '__main__':
    main()
