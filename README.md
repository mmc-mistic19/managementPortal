# Management Portal for AIL multitenant instance

This addon provides a web portal to manage terms in an AIL instance used by multiple companies.

![managementPortal](./managementPortal.PNG?raw=true "Management portal")

About AIL framework: [https://github.com/CIRCL/AIL-framework](https://github.com/CIRCL/AIL-framework)

## Installation

Type these command lines for a fully automated installation (asks for the AIL framework instance's installation path):

```bash
git clone https://github.com/mmc-mistic19/managementPortal.git
cd managementPortal
chmod +x previousConfigurations.sh
./previousConfigurations.sh
```

## Usage
Activate the virtual enviroment and run the flask server. By default server runs in port 4000.

```bash
source managementPortal/bin/activate
python3 managementPortal.py
```
Default user and password: admin/password

## Manage users and companies
Automated scripts to configure users, companies and relationships are provided in the [dbManagement](dbManagement) folder. More details available in [HOWTO.md](dbManagement/HOWTO.md).

## License
```
    Copyright (c) 2019 mmc-mistic19

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
