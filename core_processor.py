import utils
import os
import re
from functools import reduce

SERVICE_DEFAULTS = {"service": {"base": "service"},
                    "worker": {"base": "worker"},
                    "static": {"base": "service",
                               "default_options": ["behind-alb", "fixed-count", "client"]},
                    "client": {"base": "service",
                               "default_options": ["behind-alb"]},
                    "proxy": {"base": "service",
                              "default_options": []}}
OPTIONS_EDGE_CASES = {"fixed-count": {
    "alias": "singleton",
    "extra_updates": {
        "Parameters": {
            "TaskCount": {
                "Default": 1,
                "AllowedValues": [0, 1]
            }}}}}


def process_extra_modules(metadata, template):
    if 'modules' in metadata:
        print("Found modules, adding to template...")
        for module in metadata['modules']:
            add_module(template, module, metadata['type'])
    else:
        print("No extra modules found.")


def process_options(template, project_type, options):
    for key, item in options.items():
        add_module(template, item["path"], project_type, full_path=True, replace_value={key: item["value"]},
                   doc_index=0 if item.get("is_positive") else 1)
        if extra := item.get("extra_updates"):
            utils.merge(template, extra)


def add_module(template, metadata_module, project_type, full_path=False, replace_value=None, doc_index=0):
    if full_path:
        identifier = ""
        path = metadata_module
    else:
        identifier = metadata_module.get("identifier", "")
        path = f"{project_type}/modules/{metadata_module['moduleName']}"
    read_module(template, metadata_module, identifier, path, replace_value, doc_index)
    if os.path.exists(commons_path := path.replace(project_type, "commons")):
        read_module(template, metadata_module, identifier, commons_path, replace_value, doc_index)


def read_module(template, metadata_module, identifier, path, replace_value, doc_index=0):
    module = utils.load_module(path, identifier, doc_index)
    if module:
        parameters = module.get("Parameters", [])
        if isinstance(metadata_module, dict):
            for parameter in parameters:
                if default := metadata_module.get(parameter[:-len(identifier)],
                                                  metadata_module.get(parameter[:-len("Param" + identifier)])):
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
        paths = [f"{base_path}{f}" for f in os.listdir(base_path)]
        options = {}
        for path in paths:
            name = path[path_len:-5]
            if edge_case := OPTIONS_EDGE_CASES.get(name):
                name = edge_case["alias"]
            value = service_options.get(name)
            options[name] = {"path": path, "value": value, "is_positive": utils.is_positive(value)}
            if edge_case and utils.is_positive(value):
                options[name].update({"extra_updates": edge_case.get("extra_updates"), "edgeCase": True})
        return options
    else:
        return {}


def update_description(template, options, metadata):
    variables = []
    options.pop(metadata["type"].lower(), None)
    for k, v in options.items():
        if v.get("is_positive"):  # ugly!, clean this not not
            variables.append(k)
    if modules := metadata.get('modules'):
        for module in modules:
            if (module_name := module["moduleName"][:-5]) not in variables:
                variables.append(module_name)
    template["Description"] = f"Template to launch {metadata['type']} ({', '.join(variables)})"


def process_variants(options, project_type, defaults):
    options[project_type] = True
    for option in defaults.get("default_options", []):
        options[option] = True
    return defaults["base"]


def process_template(metadata):
    project_type = metadata['type'].lower()
    base_options = metadata.get(f'{project_type}Options', {})
    if project_type in SERVICE_DEFAULTS:
        project_type = process_variants(base_options, project_type,
                                        SERVICE_DEFAULTS[project_type])
        template = utils.load_ecs_service_core(utils.load_yaml_file(f"{project_type}/base.yaml", True))
    else:
        template = utils.load_yaml_file(f"{project_type}/base.yaml", True)

    options = get_options(project_type, base_options)
    process_options(template, project_type, options)
    process_extra_modules(metadata, template)
    update_description(template, options, metadata)
    return template
