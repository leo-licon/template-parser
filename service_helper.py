import utils
from core_processor import *

def process_base_template(metadata, template):
    process_base_template_generic(metadata, template, "service", service_extra_options)

def service_extra_options(template, options):
    print("Setup extra properties in service")
    task_properties = utils.find("Resources.ECSTask.Properties", template)
    task_container_definitions = task_properties['ContainerDefinitions']
    if utils.is_positive(options.get('fargate')):
        repo_container = dict(PortMappings=[{"ContainerPort": "\\!Ref ECSContainerPort"}])
    else:
        repo_container = dict(
            MountPoints=[
                {"ContainerPath": "/mnt/shared",
                 "SourceVolume": "\\!Sub '${RepoName}-SharedStorage'"},
            ],
            PortMappings=[
                {"ContainerPort": "\\!Ref ECSContainerPort"},
                {"HostPort": 0},
            ]
        )
    if utils.is_positive(options.get('vMajor')):
        repo_container.update(dict(Name="\\!Ref RepoName"))
    task_container_definitions[0].update(repo_container)
