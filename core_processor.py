import utils
import os
import re
from functools import reduce

__all__ = ["process_extra_modules", "add_module", "process_options", "get_options", "process_base_template_generic"]


def process_extra_modules(metadata, template):
    if 'modules' in metadata:
        print("Found modules, adding to template...")
        for module in metadata['modules']:
            add_module(template, module, metadata['type'])
    else:
        print("No extra modules found.")


def process_options(template, project_type, options):
    print(options)
    for key, item in options.items():
        add_module(template, item["path"], project_type, full_path=True, replace_value={key: item["value"]})


def add_module(template, metadata_module, project_type, full_path=False, replace_value=None):
    print(metadata_module)
    identifier = ""
    if full_path:
        path = metadata_module
    else:
        identifier = metadata_module.get("identifier", "")
        path = f"{project_type}/modules/{metadata_module['moduleName']}"
    module = utils.load_module(path, identifier)

    parameters = module.get("Parameters", [])

    if identifier:
        for parameter in parameters:
            if default := metadata_module.get(parameter[:-len(identifier)]):
                parameters.get(parameter)['Default'] = default
    if replace_value:
        k = next(iter(replace_value))
        if (k + "Param") in module.get("Parameters", {}):
            module["Parameters"][k + "Param"]['Default'] = replace_value[k]
    reduce(utils.merge, [template, module])


def get_options(project_type, service_options):
    base_path = f"{project_type}/options/"
    path_len = len(base_path)
    if os.path.exists(base_path):
        paths = [f"{base_path}{f}" for f in os.listdir(base_path) if
                 not re.match(r'^not-.*.yaml', f)]
        print(f'options found: {paths}')
        options = {}
        for path in paths:
            name = path[path_len:-5]
            value = service_options.get(name)
            if not utils.is_positive(value):
                not_path = f'{path[:path_len]}not-{path[path_len:]}'
                if os.path.exists(not_path):
                    path = not_path
                else:
                    path = None
            if path:
                options[name] = {"path": path, "value": value}
        return options
    else:
        return {}


def process_base_template_generic(metadata, template, type, extra_options_funct=None):
    base_options = metadata.get(f'{type}Options', {})
    options = get_options(type, base_options)
    if extra_options_funct:
        extra_options_funct(template, options)
    process_options(template, type, options)
