<h1 align="center">Welcome to kismet-csv-parser 👋</h1>
<p>
  <img alt="Version" src="https://img.shields.io/badge/version-0.0.1-blue.svg?cacheSeconds=2592000" />
  <a href="#" target="_blank">
    <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg" />
  </a>
</p>

> Uses mac addresses from a kismet csv to search for matches in a wigle csv and mac address vendor csv. Vendor csv provided.
> Also allows downloading of wigle csv via the wigle api.

## Install

Only requests and pandas are needed as dependencies for the script. Requests being the most optional of the
two, being only used to access the wigle api.

Obviously, either poetry or pipenv are the recommended means of installation, as they establish a virtual
environment to install dependencies into and run the script from.

```sh
`poetry install`
# OR
`pipenv install`
# OR
`python -m pip install requests pandas`
```

### Configuration

This project uses a configuration script for setting variables that would be too burdensome to include in the
command line. Be sure to edit it and add the information required. This configuration file should be located
within the same folder your run the script from (i.e. the repository folder). Also a csv file is included in
the repository that provides a listing of all mac address prefixes as designated by the IEEE. This file should
also be left in the repository folder, but is required to be designated on the command line with a flag.

## Usage

The following options will output the help documentation for the script.

```sh
`poetry run python kismet-parser.py -h`
# OR
`pipenv run python kismet-parser.py -h`
# OR
`python kismet-parser.py -h`
```

## Author

👤 **Anoduck**

* Website: http://anoduck.com
* Github: [@anoduck](https://github.com/anoduck)

## Show your support

Give a ⭐️ if this project helped you!

***
_This README was generated with ❤️ by [readme-md-generator](https://github.com/kefranabg/readme-md-generator)_
