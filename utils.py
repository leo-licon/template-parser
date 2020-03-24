import yaml
import os

OUT_PATH = 'finalTemplates'
if not os.path.exists(OUT_PATH):
    os.mkdir(OUT_PATH)


def find(element, dict):
    keys = element.split('.')
    rv = dict
    for key in keys:
        rv = rv[key]
    return rv


def get_base_template(type):
    with open(f"{type}/base.yaml", 'r') as stream:
        #        ^..^         Ugly replace here :(
        #       ( oo )   )~
        #         ,,   ,,
        base = stream.read().replace("!", "\\!")
        return yaml.load(base, Loader=yaml.SafeLoader)


def load_metadata(path='metadata.yaml'):
    print(f"loading metadata from {path}")
    with open(path, 'r') as metadata_file:
        return yaml.load(metadata_file.read(), Loader=yaml.SafeLoader)


def load_module(module_path, module_key):
    print(f"loading {module_path}")
    with open(module_path) as stream:
        base = stream.read().replace("!", "\\!")
        template = yaml.load(base, Loader=yaml.SafeLoader)
        names = []
        for section in ("Parameters", "Resources"):
            names.extend([key for key in template.get(section, {}).keys()])
        for name in names:
            base = base.replace(name, (name + module_key))
        template = yaml.load(base, Loader=yaml.SafeLoader)
        return template


def write_template(template):
    with open(f'{OUT_PATH}/finalTemplate.yaml', mode='wt', encoding='utf-8') as outputTemplate:
        outputTemplate.write(yaml.dump(template, width=1000, sort_keys=False).replace("\\!", "!"))


def is_positive(value=None):
    return False if not value or str(value).lower() in ("no", 0, "", "nope", "false") or "no" in str(
        value).lower() else True


def merge(a, b, path=[]):
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            elif isinstance(a[key], list):
                a[key].extend(b[key])
            elif isinstance(a[key], (str, int)):
                a[key] = b[key]
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
