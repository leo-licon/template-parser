import yaml
import os
import itertools

OUT_PATH = 'outputs'
if not os.path.exists(OUT_PATH):
    os.mkdir(OUT_PATH)


def find(element, source_dict):
    keys = element.split('.')
    rv = source_dict
    for key in keys:
        rv = rv[key]
    return rv


def load_yaml_file(path, replace=False):
    print(f"loading {path}")
    with open(path, 'r') as stream:
        base = stream.read().replace("!", "\\!") if replace else stream.read()
        return yaml.load(base, Loader=yaml.SafeLoader)


def load_module(module_path, module_key, doc_index=0):
    print(f"loading {module_path}")
    with open(module_path) as stream:
        base = stream.read().replace("!", "\\!")
        template = get_document_on_index(base, doc_index)
        if template:
            names = []
            for section in ("Parameters", "Resources"):
                names.extend([key for key in template.get(section, {}).keys()])
            for name in names:
                base = base.replace(name, (name + module_key))
            template = get_document_on_index(base, doc_index)
            return template


def get_document_on_index(base, doc_index):
    templates = yaml.load_all(base, Loader=yaml.SafeLoader)
    return next(itertools.islice(templates, doc_index, None))


def write_template(template, project_type):
    with open(f'{OUT_PATH}/{project_type}.yaml', mode='wt', encoding='utf-8') as outputTemplate:
        template = sort_template(template)
        parsed = yaml.dump(template, width=1000, sort_keys=True).replace("\\!", "!")
        outputTemplate.write(parsed)
        return parsed


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
                for i, j in itertools.zip_longest(a[key], b[key]):
                    if i and j:
                        merge(i, j)
                    elif j:
                        a[key].append(j)
                    else:
                        break
            elif isinstance(a[key], (str, int)):
                a[key] = b[key]
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


def load_ecs_service_core(template):
    commons = load_yaml_file("commons/ecs-service-base.yaml", True)
    return merge(commons, template, [])


def sort_template(template):
    template_forrmated = {}
    ordered_sections = {"Parameters": ["Type", "Description", "Default"],
                        "Resources": ["Type", "DependsOn", "Condition", "Metadata", "Properties"]}
    for section in (
            "AWSTemplateFormatVersion", "Description", "Parameters", "Mappings", "Conditions", "Resources", "Outputs"):
        if value := template.get(section):
            if section in ordered_sections:
                value = reorder_items(value, ordered_sections[section])
            template_forrmated[section] = value
    return template_forrmated


def reorder_items(items, keys):
    ordered_items = {}
    for name, content in items.items():
        ordered_item = {}
        for key in keys:
            if (v := content.pop(key, None)) is not None:
                ordered_item.update({key: v})
        ordered_item.update(content)
        ordered_items.update({name: ordered_item})
    return ordered_items
