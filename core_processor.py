import utils
import os
import re
from functools import reduce

ECS_SERVICE_TYPES = ["service", "worker"]


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

    if full_path:
        identifier = ""
        path = metadata_module
    else:
        identifier = metadata_module.get("identifier", "")
        path = f"{project_type}/modules/{metadata_module['moduleName']}"
    read_module(template, metadata_module, identifier, path, replace_value)
    if os.path.exists(commons_path := path.replace(project_type, "commons")):
        read_module(template, metadata_module, identifier, commons_path, replace_value)


def read_module(template, metadata_module, identifier, path, replace_value):
    module = utils.load_module(path, identifier)
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


def update_description(template, options, metadata):
    variables = []
    for k, v in options.items():
        if not "not-" in v["path"]:  # bad bad, clean this not not
            variables.append(k)
    if modules := metadata.get('modules'):
        for module in modules:
            if (module_name := module["moduleName"][:-5]) not in variables:
                variables.append(module_name)
    template["Description"] = f"Template for {metadata['type']} ({', '.join(variables)})"


def process_template(metadata):
    project_type = metadata['type'].lower()
    template = utils.load_yaml_file(f"{project_type}/base.yaml", True)
    if project_type in ECS_SERVICE_TYPES:
        template = utils.load_ecs_service_core(template)
    base_options = metadata.get(f'{project_type}Options', {})
    options = get_options(project_type, base_options)
    process_options(template, project_type, options)
    process_extra_modules(metadata, template)
    update_description(template, options, metadata)
    return template
