import json
from contextlib import contextmanager
from pathlib import Path
from typing import Union


@contextmanager
def jsonfile(filepath: Union[Path, str], default=None):
    filepath = Path(filepath)
    object = default
    obj_copy = None
    try:
        object = json.loads(filepath.read_text(encoding='utf-8'))
        import copy
        obj_copy = copy.deepcopy(object)
        yield object
    except Exception as e:
        print(e)
        yield object
    finally:
        if object != obj_copy:
            print('write...')
            filepath.write_text(json.dumps(object, indent=4, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    with jsonfile(Path(__file__).with_name('test.json'), {}) as obj:
        obj["a"] = 'b'
        print(obj)
