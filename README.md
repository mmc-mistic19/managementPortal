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

## License
[MIT](https://choosealicense.com/licenses/mit/)
