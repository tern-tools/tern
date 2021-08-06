import subprocess

tests = [
    'tern report -i photon:3.0',
    'python3 setup.py sdist && ' 
    'docker build -t ternd -f ci/Dockerfile . && '
    './docker_run.sh ternd "report -i golang:alpine"',
    'tern report -i golang:alpine',
    'python tests/test_class_command.py',
    'python tests/test_class_file_data.py',
    'python tests/test_class_image.py',
    'python tests/test_class_image_layer.py',
    'python tests/test_class_notice.py',
    'python tests/test_class_notice_origin.py',
    'python tests/test_class_origins.py',
    'python tests/test_class_package.py',
    'python tests/test_class_template.py',
    'tern report -f spdxtagvalue -i photon:3.0',
    'tern lock samples/single_stage_tern/Dockerfile',
    'tern report -i debian:buster',
    'tern report -i alpine:3.9',
    'tern report -i archlinux:latest',
    'tern report -i centos:7',
    'tern report -i node:12.16-alpine',
    'python tests/test_analyze_default_dockerfile_parse.py',
    'python tests/test_analyze_common.py',
    'tern report -i golang:alpine',
    'tern report -d samples/alpine_python/Dockerfile',
    'tern report -w photon.tar',
    'python tests/test_load_docker_api.py',
    'tern report -f yaml -i photon:3.0',
    'tern report -f json -i photon:3.0',
    'tern report -f spdxjson -i photon:3.0',
    'tern report -f html -i photon:3.0',
    'tern report -f spdxtagvalue -i photon:3.0 -o spdx.spdx && '
    'java -jar tools-java/target/tools-java-*-jar-with-dependencies.jar '
    'Verify spdx.spdx', 
    'tern report -f spdxjson -i photon:3.0 -o spdx.json && '
    'java -jar tools-java/target/tools-java-*-jar-with-dependencies.jar '
    'Verify spdx.json',
    'python tests/test_util_general.py',
    'python tests/test_analyze_default_filter.py',
    'python tests/test_class_command.py',
    'python tests/test_class_docker_image.py'
]

for t in tests:
    subprocess.check_output(t, shell=True)         
