from pathlib import Path

from jsonfile import jsonfile


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
