#### 11-08-2023

- The build number and the `lib_version` in the `conf.json` will not be updated via bash script and instead from the pyfhirsdc itself.
- Added environment variable to `conf.json`, the accepted values are `dev` or `prod`.
- When the environment variable is set to `dev` the patch version number will be updated.
- When the environment varaible is set to `prod` the minor version number will be updated.
- Follow the `conf.example.json` file for a template for `conf.json`