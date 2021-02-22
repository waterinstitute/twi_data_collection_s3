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

Once installed (i.e. the src path is part of the PYTHONPATH), you can use the module as follows:

```bash
python -m metadata_collector --help
Usage: python -m metadata_collector [OPTIONS]

  This app will collect the metadata from the buckets for a project and
  create the feature-class map with them.

Options:
  --project TEXT                  Id of the project, default: TEST  [default:
                                  TEST]

  --process_all                   Process all the documents, ignoring the
                                  already seen lists  [default: False]

  -b, --bucket TEXT               the bucket to scan (optional if you provide
                                  the project name), you can use multiple
                                  buckets using: -b bucket1 -b bucket2 ...

  -o, --output_format [GeoJSON|GPKG|Shapefile|CSV]
                                  [default: GeoJSON]
  --output_name TEXT              output name without extension (will be added
                                  according to the format)  [default: output]

  --generate_plot                 generate a plot of the map  [default: False]
  --hucs_gdb PATH                 [default: ./data/hucs.gdb]
  --agol_credentials TEXT         a json including  username,  password,
                                  endpoint (optional, will use the twiotg
                                  instance by default),  folder (optional,
                                  will use / by default), and  tags
                                  (optional). example:

                                  --agol_credentials '{   "username":
                                  "theUsername",   "password": "thePassword",
                                  "endpoint":
                                  "https://theagolinstance.maps.arcmap.com",
                                  "folder": "/",   "tags": ["map", "metadata"]
                                  }'

  --help                          Show this message and exit.
```

It requires the hucs.gdb file (or a shapefile), you can set the path using the option `--hucs_gdb <the file location>`, or it will try to use the default location.

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

For test, we use [MinIO](https://min.io). Make sure to start the server, pointing to the appropriated folder, before testing. We can add a minio binary to the virtual environment  for convenience:

```bash
cd .venv/bin
wget https://dl.min.io/server/minio/release/linux-amd64/minio
```

Then, from the project root, we could start the server using:

```bash
minio server a_test_folder 2>&1 >logs/minio.log &
```

In MinIO, the folders on the test folders will be used as buckets.

Also, when activating the environment again, in a new session, you may get a message indicating that GDAL_DATA is not set, to avoid this you can add this line to the `.venv/bin/activate` script:

```bash
export GDAL_DATA=$VIRTUAL_ENV/lib/python3.8/site-packages/fiona/gdal_data/
```



## Development standards

Code must be documented. We use click to define the CLIs. We use black as formatter (the pre-commit hook will take care of it, if you follow the previous instructions).

We use bandit to detect security problems. In the travis configuration bandit results are informative only (they doesn't mark the build as failed).

The main branch on Github is intended to have code common to different data collection projects. You should either fork or create a new branch to add code/documentation specific to one project.
