'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

'''
Report formatting for different types of reports and report content
'''


# formatting variables
layer_id = ''
package_name = ''
package_version = ''
package_url = ''
package_license = ''
package_info_retrieval_errors = ''
package_info_reporting_improvements = ''

# general formatting
# report disclaimer
disclaimer = f'''This report was generated using the Tern Project\n\n'''
# cache
retrieve_from_cache = f'''Retrieving packages from cache for layer ''' \
    f'''{layer_id}:\n\n'''
# command library
base_listing = f'''Direct listing in command_lib/base.yml:\n\n'''
snippet_listing = f'''Direct listing in command_lib/snippets.yml:\n\n'''
invoke_for_base = f'''Using invoke listing in command_lib/base.yml:\n\n'''
invoke_for_snippets = f'''Using invoke listing in command_lib/snippets.yml''' \
    f''':\n\n'''
invoke_in_container = '''\tin container:\n'''
invoke_on_host = '''\ton host:\n'''
# package information
package_info = f'''Package: {package_name}\nVersion: {package_version}\n''' \
    f'''Project URL: {package_url}\nLicense: {package_license}\n\n'''
# notes
package_notes = f'''Errors: {package_info_retrieval_errors}\n''' \
    f'''Improvements: {package_info_reporting_improvements}\n'''
# demarkation
package_demarkation = f'''------------------------------------------------''' \
    f'''\n\n'''

# report formatting for dockerfiles

# dockerfile variables
base_image_instructions = ''
dockerfile_instruction = ''

# dockerfile report sections
dockerfile_header = '''Report from Dockerfile\n'''
dockerfile_base = f'''Base Image: {base_image_instructions}\n'''
dockerfile_line = f'''Instruction Line: {dockerfile_instruction}\n'''
