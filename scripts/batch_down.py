import json
import logging
import os
import sys
from pathlib import Path


def json_from_file(filepath, default_value=None):
    for enc in ['utf-8', 'gbk']:
        try:
            with open(filepath, encoding=enc) as fp:
                return json.loads(fp.read())
        except Exception:
            pass
    return default_value


def main():
    record = json_from_file(Path(__file__).parent.with_name('record.json'))
    script_path = Path(__file__).with_name('y2b_video2m3u8.py')
    for item in record:
        name = item.get('name')
        url = item.get('source')
        cmd = f'{sys.executable} "{script_path}" "{url}" 1080p --name "{name}"'
        ret_code = os.system(cmd)
        assert ret_code == 0, '出错了×'
        

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.exception(e)
