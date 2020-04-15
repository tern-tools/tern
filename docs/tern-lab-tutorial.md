# What is Tern

Tern is an inspection tool to find the metadata of the packages installed in a container image. Tern gives you a deeper understanding of your container's bill of materials so you can make better decisions about your container based infrastructure, integration and deployment strategies. It's also a good tool if you are curious about the contents of the container images you have built. This lab will show you how you can use Tern to inspect a Photon container image and also inspect the image created using a Dockerfile.

## Environment Overview

This lab was designed as a Strigo tutorial but can also be followed if you are working in a Linux environment. Your lab environment is hosted with a cloud server instance. This instance is accessible by clicking the "My Lab" icon on the left of your Strigo web page. You can access the terminal session using the built-in interface provided by Strigo or feel free to SSH directly as well (instructions will appear in the terminal).

## Prerequisites

### Step 1: Install environment dependencies.

```
$ sudo apt install python3 python3-pip python3-venv attr git
```

### Step 2: Create a python3 virtual environment:

```
$ python3 -m venv ternenv  
$ cd ternenv  
$ source bin/activate  
```

## Installing Tern

### Step 1: Ensure required dependencies are available.

```
$ pip3 install wheel
```

### Step 2: Install Tern from PyPI.

```
$ pip3 install tern
```

Tern is now ready to be used to inspect Docker container images.

## Running Tern

### Option 1: Generate the default report for a container image

```
$ tern report -o output.txt -i photon:3.0
```

Look at the report generated in `output.txt`.

```
$ vi output.txt
```

Specifically, look for:  
 a) Information about the Base OS  
 b) The commands used to generate each layer (only one layer for Photon)
 c) The list of packages in the layer  
 d) The list of licenses in the layer  
 e) The summary of licenses found in the container

Repeat as desired for any Docker container image of your choosing.

### Option 2:  Generate a YAML report for the container image

```
$ tern report -i photon:3.0 -f yaml -o yaml.txt
```

Look at the report generated in `yaml.txt`. Specifically, notice:  
 a) The license associated with each package  
 b) The `proj_url` for each package which points you to more information about the package  

Repeat as desired for any Docker container image of your choosing.

### Option 3: Generate a JSON report for the container image

```
$ tern report -i photon:3.0 -f json -o json.txt
```

Repeat as desired for any Docker container image of your choosing.

### Option 4: Generate a SPDX tag-value report for the container image

[SPDX](https://spdx.org/) is a format developed by the Linux Foundation to provide a standard way of reporting license information. Many compliance tools are compatible with SPDX. Tern follows the SPDX [specifications](https://spdx.org/specifications) specifically the tag-value format which is the most compatible format with the toolkit the organization provides. The tag-value format is the only SPDX format Tern supports. There are conversion tools available [here](https://github.com/spdx/tools) (some still in development). You can read an overview of the SPDX tag-value specification [here](https://github.com/tern-tools/tern/blob/master/docs/spdx-tag-value-overview.md) and about how Tern maps its properties to the keys mandated by the spec [here](https://github.com/tern-tools/tern/blob/master/docs/spdx-tag-value-mapping.md).

#### Step 1: Generate the SPDX tag-value report

```
$ tern report -i photon:3.0 -f spdxtagvalue -o spdx.txt
```

#### Step 2: Check if your SPDX report validates

Navigate to the [SPDX Validation Tool](http://13.57.134.254/app/validate/). Upload your recently generated `spdx.txt` file and see if it validates.

Repeat steps 1 & 2 as desired for any Docker container image of your choosing.

## Option 5: Generate a default report from a Dockerfile

Copy and paste the following Dockerfile into a new file `demo/Dockerfile`.

```
FROM photon:3.0  
  
CMD ["/bin/echo", "Hello, Tern Lab User!"]
```

You can use create the new Dockerfile using the following commands:

```
$ mkdir demo
$ vi demo/Dockerfile
# Once inside the editor, hit 'i'
# Paste the Dockerfile above or re-type it
# Hit 'esc'
# Type 'Shift' + ':' then type 'wq'
# Hit 'enter'
```

Run Tern using the newly-created Dockerfile. You should see a similar list of packages in the output report as you did in the first `output.txt` file you created.

```
$ tern report -d demo/Dockerfile -o dockerfile.txt
```
	
## Get Involved with Tern

Do you have questions about Tern? Do you think it can do better? Would you like to make it better? You can get involved by giving your feedback and contributing to the code, documentation and conversation!

Please read our [code of conduct](https://github.com/tern-tools/tern/blob/master/CODE_OF_CONDUCT.md) and see our [CONTRIBUTING.md](https://github.com/tern-tools/tern/blob/master/CONTRIBUTING.md) for details on the project and the process for submitting pull requests.

## Authors

* **Nisha Kumar** - nishak@vmware.com
* **Rose Judge** - rjudge@vmware.com

## License

Tern is licensed under the The BSD-2 license - see [LICENSE.txt](https://github.com/tern-tools/tern/blob/master/LICENSE.txt) for more information.
