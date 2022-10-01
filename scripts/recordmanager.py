import hashlib
from pathlib import Path

from dingtalkupload import upload_image

from jsonfile import jsonfile


def md5_for_file(filename, block_size=2**16):
    md5 = hashlib.md5()
    with open(filename, 'rb') as fp:
        for chunk in iter(lambda: fp.read(block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def read_record() -> list:
    record_file = Path(__file__).parent.with_name('record.json')
    assert record_file.exists(), f'记录文件不存在：{record_file.absolute()}'
    with jsonfile(record_file, []) as obj:
        return obj


def get_item_by_name(name):
    record = read_record()
    for item in record:
        if item.get("name") == name:
            return item
    return {}


def get_source_by_name(name):
    item = get_item_by_name(name)
    return item.get('source')


def get_update_time_by_name(name):
    item = get_item_by_name(name)
    return item.get('update_time')


def update_item(new_item: dict):
    name = new_item.get('name')
    assert name, 'name不能为空'
    record_file = Path(__file__).parent.with_name('record.json')
    assert record_file.exists(), f'记录文件不存在：{record_file.absolute()}'
    with jsonfile(record_file, []) as obj:
        found_item = None
        for item in obj:
            if item.get('name') == name:
                found_item = item
                break
        if found_item:
            found_item.update(new_item)
        else:
            obj.append(new_item)


def update_source_for_name(name, source):
    update_item({'name': name, 'source': source})


def update_time_for_name(name, update_time):
    update_item({'name': name, 'update_time': update_time})


def sync_all_covers():
    record_file = Path(__file__).parent.with_name('record.json')
    assert record_file.exists(), f'记录文件不存在：{record_file.absolute()}'
    cover_dir = Path('cover')
    with jsonfile(record_file, []) as obj:
        for item in obj:
            name = item.get('name', '')
            img_file = cover_dir.joinpath(f'{name}.jpg')
            img_md5 = md5_for_file(img_file)
            if img_md5 != item.get('cover_md5'):
                cover_url = upload_image(str(img_file))
                item['cover_url'] = cover_url
                item['cover_md5'] = img_md5
