# TWI Data Collection - AWS S3- AGOL integration

This project includes the integration script for the TWI institute data collection projects. It also defines a metadata format, a folder naming convention, and an AGOL feature class structure.

This project includes a notebook demonstrating the approach (in docs/notebooks folder).

You need to configure your credentials in the `$HOME/.aws/credentials` file, using your project names to separate the different execution environments.



```ini
[LWI]
aws_access_key_id = <an access key>
aws_secret_access_key = <a secret access key>
[GLO]
aws_access_key_id = <an access key>
aws_secret_access_key = <a secret access key>
[TEST]
aws_access_key_id = <the minio access key>
aws_secret_access_key = <the minio secret key>
```



## Development environment

You will need virtualenv and python3.8+. In a ubuntu box you can install it using

```bash
sudo apt install python3 virtualenv
```

Then, you can create a virtual environment, activate it, and install the dependencies:

```bash
virtualenv -p python3 .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This project uses pre-commit hooks, so you need to run:

```bash
pre-commit install
```

 the first time you clone your project.

For test we use minio. Make sure to start the server, pointing to the appropriated folder, before testing.

## Development standards

Code must be documented. We use click to define the CLIs. We use black as formatter (the pre-commit hook will take care of it, if you follow the previous instructions).

We use bandit to detect security problems. In the travis configuration bandit results are informative only (they doesn't mark the build as failed).

The main branch on Github is intended to have code common to different data collection projects. You should either fork or create a new branch to add code/documentation specific to one project.
