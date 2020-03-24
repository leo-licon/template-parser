""" Creates a stack template """
import utils
import lambda_helper #required
import service_helper #required
import worker_helper #required
import task_helper #required

metadata = utils.load_metadata("service-metadata.yaml")
project_type = metadata['type']
template = utils.get_base_template(metadata['type'])
helper = globals()[project_type+"_helper"]
helper.process_base_template(metadata, template)
helper.process_extra_modules(metadata, template)
utils.write_template(template)
