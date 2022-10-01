import json
import math
import os
import re
from datetime import datetime
from pathlib import Path
from urllib import parse

from recordmanager import (get_update_time_by_name, read_record, sync_all_covers, update_time_for_name)


def updateEnv(name, value):
    os.popen(f'echo "{name}={value}" >> $GITHUB_ENV')


def encodeurl(url=''):
    # 参考：https://stackoverflow.com/a/6618858
    return parse.quote(url, safe='~@#$&()*!+=:;,.?/\'')


def json_from_file(filepath, default_value=None):
    for enc in ['utf-8', 'gbk']:
        try:
            with open(filepath, encoding=enc) as fp:
                return json.loads(fp.read())
        except Exception:
            pass
    return default_value


def json_write_file(obj, filepath):
    with open(filepath, 'w', encoding='utf-8') as fp:
        fp.write(json.dumps(obj, ensure_ascii=False, indent=4))


def gen_new_tag():
    # 获取当前分支最新tag
    select_cmd = 'Select -First 1' if os.name == 'nt' else 'head -n 1'
    fp = os.popen(f'git tag --sort=-v:refname -l "*.*.*" | {select_cmd}')
    # fp = os.popen('git describe --abbrev=0 --tags')
    tag = fp.read().strip()
    major = 0
    minor = 0
    build = 0
    for i, s in enumerate(tag.split('.')):
        result = re.search(r'(\d+)', s)
        v = int(result.group(1)) if result else 0
        if i == 0:
            major = v
        elif i == 1:
            minor = v
        elif i == 2:
            build = v
        else:
            break
    while True:
        build = build + 1
        if (build > 99):
            minor = minor + 1
            build = 0
        if (minor > 99):
            major = major + 1
            minor = 0
            build = 0
        tag = f'{major}.{minor}.{build}'
        fp = os.popen(f'git tag -l {tag}')
        matched_tag = fp.read().strip()
        if len(matched_tag) == 0:
            break
    return tag


def parseDuration(filepath):
    with open(filepath, encoding='utf-8') as fp:
        m3u8_content = fp.read()
    duration = 0
    for item in re.findall(r'#EXTINF:(.+?),', m3u8_content):
        duration += max(0, float(item))
    i = math.floor(duration % 60)
    n = math.floor(duration / 60 % 60)
    r = math.floor(duration / 3600)
    if r > 0:
        time_formated = ':'.join([f'{r:02}', f'{n:02}', f'{i:02}'])
    else:
        time_formated = ':'.join([f'{n:02}', f'{i:02}'])
    return time_formated


def get_update_time(filepath):
    # text = Path(filepath).read_text(encoding='utf-8')
    # results = re.findall('https?://.+', text)
    # if not results:
    #     return None
    # result = re.search(r'(\d{10,})', results[-1])
    # if not result:
    #     return None
    # return int(result.group(1))
    return get_update_time_by_name(Path(filepath).stem)


def get_file_commit_time(filepath):
    # 获得文件更新时间
    cmd = f'git log -1 --format="%ad" -- "{filepath}"'
    proc = os.popen(cmd)
    time_str = proc.read().strip()
    if time_str.strip():
        timestamp = datetime.strptime(time_str, '%a %b %d %H:%M:%S %Y %z').timestamp()
        return int(timestamp)
    return None


def remove_unused_cover():
    path = Path('cover')
    for item in path.glob('*.jpg'):
        if not Path('playlist').joinpath(f'{item.stem}.m3u8').exists():
            item.unlink()


def upload_cover():
    sync_all_covers()


if __name__ == '__main__':
    tag = gen_new_tag()
    # 保存tag到环境变量 push时要用到
    updateEnv('new_tag', tag)
    branch = os.environ.get('GITHUB_REF_NAME')
    repo_full = os.environ.get('GITHUB_REPOSITORY')

    remove_unused_cover()
    upload_cover()

    infos = []
    playlist_dir = Path('playlist')
    for item in read_record():
        mv_name = item.get('name', '')
        cover_url = item.get('cover_url', '')
        filepath = str(playlist_dir.joinpath(f'{mv_name}.m3u8'))
        # url = parse.urljoin(f'https://cdn.jsdelivr.net/gh/{repo_full}@{tag}/', filepath)
        # url = encodeurl(url)

        # cover_url = parse.urljoin(f'https://cdn.jsdelivr.net/gh/{repo_full}@{tag}/', f'cover/{item.stem}.jpg')
        # cover_url = encodeurl(cover_url)
        timestamp = int(datetime.now().timestamp())
        # cover_url = parse.urljoin(f'https://raw.githubusercontents.com/{repo_full}/{branch}/', f'cover/{item.stem}.jpg?t={timestamp}')
        cover_url = encodeurl(cover_url)

        duration = parseDuration(filepath)
        timestamp = get_update_time(filepath)
        if not timestamp:
            timestamp = get_file_commit_time(filepath)
            if not timestamp:
                timestamp = int(datetime.now().timestamp())
            update_time_for_name(Path(filepath).stem, timestamp)

        raw_url = parse.urljoin(f'https://raw.githubusercontent.com/{repo_full}/{branch}/', filepath)
        raw_url = encodeurl(raw_url)

        url = raw_url.replace('https://raw.githubusercontent.com/', 'https://raw.fastgit.org/')

        infos.append(
            {
                'name': mv_name,
                'url': url,
                'cover_url': cover_url,
                'raw_url': raw_url,
                'filepath': filepath,
                'timestamp': timestamp,
                'duration': duration
            }
        )
    # 根据时间戳从大到小排序
    infos = sorted(infos, key=lambda e: e.__getitem__('timestamp'), reverse=True)
    mv_info = []
    md_lines = []
    for item in infos:
        name = item.get('name')
        url = item.get('url')
        cover_url = item.get('cover_url')
        raw_url = item.get('raw_url')
        timestamp = item.get('timestamp')
        duration = item.get('duration')
        mv_info.append({'name': name, 'url': url, 'cover_url': cover_url, 'update_time': timestamp, 'duration': duration})
        md_lines.append(
            f'- {name}&emsp;[![](https://static.dingtalk.com/media/lALPJwKtwnCxTnIUIQ_33_20.png)](http://tools.201992.xyz/m3u8-play.html#{url})&ensp;[![](https://static.dingtalk.com/media/lALPJxRxO6ipLPsUIQ_33_20.png)]({raw_url})'
        )
    md_lines.insert(0, f'# Fallrainy的MV(共 {len(mv_info)} 支)')
    Path.write_text(Path('playlist.json'), json.dumps(mv_info, ensure_ascii=False, indent=4), encoding='utf-8')
    Path.write_text(Path('playlist/README.md'), '\n'.join(md_lines), encoding='utf-8')
