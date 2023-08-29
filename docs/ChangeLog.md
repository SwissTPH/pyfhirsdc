#### 29-08-2023

- BREAKING base library (pyfhirsdc) move inside the project because there are required, it means pfsdc. should be used instead of Base. import type: include pyfhirsdc version '1.0.0' alias pfsdc
- Version of will follow the module version


#### 21-08-2023

- When there is a reference resource linked in a profile, `targetProfile` element will now be populated and will be linked in the generated IG

#### 11-08-2023

- The build number and the `lib_version` in the `conf.json` will not be updated via bash script and instead from the pyfhirsdc itself.
- Added environment variable to `conf.json`, the accepted values are `dev` or `prod`.
- When the environment variable is set to `dev` the patch version number will be updated.
- When the environment varaible is set to `prod` the minor version number will be updated.
- Follow the `conf.example.json` file for a template for `conf.json`