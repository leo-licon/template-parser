import utils
from core_processor import *


def process_base_template(metadata, template):
    process_base_template_generic(metadata, template, "worker", service_extra_options)


def service_extra_options(template, options):
    print("Setup extra properties in worker")
    task_properties = utils.find("Resources.ECSTask.Properties", template)
    task_container_definitions = task_properties['ContainerDefinitions']
    if utils.is_positive(options.get('vMajor')):
        repo_container = dict(Name="\\!Ref RepoName")
        task_container_definitions[0].update(repo_container)
