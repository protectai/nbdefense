---
description: This section covers the installation of NB Defense on SageMaker Notebook Instances
---

# Configuring NB Defense for SageMaker Notebook Instances

## JupyterLab Extension (JLE) Installation

1.  Select the “Open JupyterLab” option when your sagemaker notebook has been provisioned.

    ![sm_notebook_1](images/sm-notebook-1.png)

    <i>Note: NB Defense JLE requires JupyterLab 3.</i>

2.  When JupyterLab opens, select “Terminal” to open a new terminal.

    ![sm_notebook_2](images/sm-notebook-2.png)

3.  When the terminal is open, type the following command to view all conda environments present on the sagemaker instance:

    ```bash
    conda info --envs
    ```

4.  You should get output similar to this:

    ![sm_notebook_3](images/sm-notebook-3.png)

    The asterisk next to an environment indicates the current (default) active environment - for sagemaker notebooks, the default active environment is always `JupyterSystemEnv`

    This is where you want to install the NB Defense JLE.

5.  Install the extension with pip (please ensure to replace your license key with {LICENSE_KEY} or get your pre-filled link from the [NB Defense web portal](https://nbdefense.protectai.com/)):

    ```bash
    pip install nbdefense_jupyter 
    ```

6.  After the installation is complete, type the following into the terminal:

    ```bash
    jupyter server extension enable nbdefense_jupyter
    ```

7.  Now that we have installed and enabled the JLE we simply need to restart the Jupyter Server with the following command:

    ```bash
    sudo systemctl restart jupyter-server
    ```

    The above command will cause you to lose connection to your terminal. The terminal window will automatically close - this is expected behavior due to the Jupyter Server restarting.

    You will be taken back to the main page of the Sagemaker JupyterLab UI.

8.  To confirm that installation was succesful, open a new terminal and run the following commands:

    ```bash
    jupyter labextension list # view installed extensions on the client
    jupyter server extension list # view installed extensions on the server
    ```

    You should see something like the following (notice how `nbdefense_jupyter` is present in both lists):

    ![sm_notebook_4](images/sm-notebook-4.png)

9.  You can now close the terminal and refresh your JupyterLab webpage (CMD+R on a Mac or CTRL+R on a Windows machine). The NBDefense JLE widget should appear on the left hand side of the JupyterLab UI:

    ![sm_notebook_5](images/sm-notebook-5.png)

10. You can now start scanning with the NB Defense JLE!

## SageMaker Lifecycle Policies

When using Sagemaker, configurations to the shipped kernels are not persisted between ‘start’ and ‘stop’ cycles of the notebook.

As such, between each ‘starting’ and ‘stopping’ of the notebook, NB Defense JLE will not be present in the kernel you may have previously installed it in. More information on this can be found [here.](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi-add-external.html)

In order to prevent having to re-install and configure NB Defense each time you ‘start’ and ‘stop’ a sagemaker instance, we can utilize a Lifecycle Policy.

Lifecycle policies will allow for the automatic installation, configuration and persistence of installed libraries and JupyterLab extensions between every ‘start’ and ‘stop’ cycle.

For the JLE you will need to provide an `on-start.sh` script as a lifecycle policy. Below is a version of the `on-start.sh` script that installs the JLE:

```bash
#!/bin/bash

set -e

# OVERVIEW
# This script installs a custom, persistent installation of conda on the Notebook Instance's EBS volume, and ensures that these custom environments are available as kernels in Jupyter.

# The on-start script uses the custom conda environment created in the on-create script and uses the ipykernel package to add that as a kernel in Jupyter.

# For another example, see:
# https://docs.aws.amazon.com/sagemaker/latest/dg/nbi-add-external.html#nbi-isolated-environment

sudo -u ec2-user -i <<'EOF'
unset SUDO_UID

source /home/ec2-user/anaconda3/bin/activate JupyterSystemEnv

# Don't forget to add your license key
pip install nbdefense_jupyter --extra-index-url https://license:{LICENSE_KEY}@api.keygen.sh/v1/accounts/protectai/artifacts

jupyter server extension enable nbdefense_jupyter

source /home/ec2-user/anaconda3/bin/deactivate

# Optionally, uncomment these lines to disable SageMaker-provided Conda functionality.
# echo "c.EnvironmentKernelSpecManager.use_conda_directly = False" >> /home/ec2-user/.jupyter/jupyter_notebook_config.py
# rm /home/ec2-user/.condarc
EOF

echo "Restarting the Jupyter server.."
# restart command is dependent on current running Amazon Linux and JupyterLab
CURR_VERSION_AL=$(cat /etc/system-release)
CURR_VERSION_JS=$(jupyter --version)

if [[ $CURR_VERSION_JS == *$"jupyter_core     : 4.9.1"* ]] && [[ $CURR_VERSION_AL == *$" release 2018"* ]]; then
	sudo initctl restart jupyter-server --no-wait
else
	sudo systemctl --no-block restart jupyter-server.service
fi
```

The above script can be customized to alter the name of the custom environment as well as the directory created that hosts the environment. This script does the following:

1. Installs the JupyterLab Extension in the `JupyterSystemEnv` environment
2. Enables the NB Defense JLE
3. Restarts the Jupyter Server so that the changes are reflected.

## Common Installation Issues

Here are some of the known issues when installing JLE on SageMaker Notebooks.

### The nbdefense-jupyter server extension fails to enable because of a jsonschema version conflict

There are dependency conflicts being shipped by Sagemaker Notebooks out of the box (at the time of this writing) with the jsonschema package. This error may manifest as

`jupyterlab-server 2.19.0 requires jsonschema>=4.17.3, but you have jsonschema 3.2.0 which is incompatible.`

Consequently, when running the command to enable the nbdefense-jupyter extension, it will give an error that there is no module named `jsonschema.protocols`:

```
Traceback (most recent call last):
File "/home/ec2-user/anaconda3/envs/JupyterSystemEnv/lib/python3.7/site-packages/jupyter_server/extension/manager.py", line 175, in _validate_name
self._module, self._metadata = get_metadata(name)
File "/home/ec2-user/anaconda3/envs/JupyterSystemEnv/lib/python3.7/site-packages/jupyter_server/extension/utils.py", line 55, in get_metadata
module = importlib.import_module(package_name)
File "/home/ec2-user/anaconda3/envs/JupyterSystemEnv/lib/python3.7/importlib/__init__.py", line 127, in import_module
return _bootstrap._gcd_import(name[level:], package, level)
File "<frozen importlib._bootstrap>", line 1006, in _gcd_import
File "<frozen importlib._bootstrap>", line 983, in _find_and_load
File "<frozen importlib._bootstrap>", line 967, in _find_and_load_unlocked
File "<frozen importlib._bootstrap>", line 677, in _load_unlocked
File "<frozen importlib._bootstrap_external>", line 728, in exec_module
File "<frozen importlib._bootstrap>", line 219, in _call_with_frames_removed
File "/home/ec2-user/anaconda3/envs/JupyterSystemEnv/lib/python3.7/site-packages/jupyter_server_fileid/__init__.py", line 2, in <module>
from .extension import FileIdExtension
File "/home/ec2-user/anaconda3/envs/JupyterSystemEnv/lib/python3.7/site-packages/jupyter_server_fileid/extension.py", line 1, in <module>
from jupyter_events.logger import EventLogger
File "/home/ec2-user/anaconda3/envs/JupyterSystemEnv/lib/python3.7/site-packages/jupyter_events/__init__.py", line 3, in <module>
from .logger import EVENTS_METADATA_VERSION, EventLogger
File "/home/ec2-user/anaconda3/envs/JupyterSystemEnv/lib/python3.7/site-packages/jupyter_events/logger.py", line 19, in <module>
from .schema_registry import SchemaRegistry
File "/home/ec2-user/anaconda3/envs/JupyterSystemEnv/lib/python3.7/site-packages/jupyter_events/schema_registry.py", line 3, in <module>
from .schema import EventSchema
File "/home/ec2-user/anaconda3/envs/JupyterSystemEnv/lib/python3.7/site-packages/jupyter_events/schema.py", line 6, in <module>
from jsonschema.protocols import Validator
ModuleNotFoundError: No module named 'jsonschema.protocols'
```

**One way to get around this issue is to install a `jsonschema` version greater than 4.0.0 using:**

```shell
pip install "jsonschema>4"
```

If you are still having trouble installing the JLE on SageMaker Notebook, please feel free to reach out to us at [support@protectai.com](mailto:support@protectai.com).
