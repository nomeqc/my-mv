import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Union


@contextmanager
def jsonfile(filepath: Union[Path, str], default=None) -> Generator[Any, None, None]:
    filepath = Path(filepath)
    object = default
    obj_copy = None
    try:
        object = json.loads(filepath.read_text(encoding='utf-8'))
        import copy
        obj_copy = copy.deepcopy(object)
        yield object
    except Exception:
        yield object
    finally:
        if object != obj_copy:
            filepath.write_text(json.dumps(object, indent=4, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    with jsonfile(Path(__file__).with_name('test.json'), {}) as obj:
        obj["a"] = 'b'
        print(obj)
