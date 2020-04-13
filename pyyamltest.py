""" Creates a stack template """
import utils
import core_processor

import boto3

cf_client = boto3.client("cloudformation")
complete_list = ["service", "task", "lambda", "worker", "static", "client", "proxy"]

for t in complete_list:
    metadata = utils.load_yaml_file(f"{t}-metadata.yaml")
    template = core_processor.process_template(metadata)
    project_type = metadata['type']
    t = utils.write_template(template, project_type)
    print("VALIDATED", template["Description"],cf_client.validate_template(TemplateBody=t))
