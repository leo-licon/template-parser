import os
import utils
import yaml
def get_templates(base_dir="currentTemplates"):
    files = []

    if os.path.exists(base_dir):
        for f in [f"{base_dir}/{f}" for f in os.listdir(base_dir)]:
            if os.path.isdir(f):
                if f.endswith(("lambda", "service", "worker", "task")):
                    files.extend(get_templates(f))
            elif f.endswith(".yaml"):
                files.append(f)
    return files
def write_template(template, path):
    with open(f'{path}.bkp', mode='wt', encoding='utf-8') as outputTemplate:
        template = utils.sort_template(template)
        parsed = yaml.dump(template, width=1000, sort_keys=True).replace("\\!", "!")
        outputTemplate.write(parsed)
        return parsed

templates = get_templates()
for template in templates:
    write_template(utils.load_yaml_file(template, True), template)