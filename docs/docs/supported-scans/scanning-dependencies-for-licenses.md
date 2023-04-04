# Third Party License Validation

NB Defense relies on the licensing reporting for packages hosted in PyPI as well as the locally stored copies of these packages where available. 

We simply parse the license information to determine if it matches licenses that are known to be friendly for commercial usage, specifically:

```python
ACCEPTED_LICENSES = [
    "Apache License 2.0",
    "Apache Software License",
    "Apache 2.0",
    "Apache-2.0",
    "BSD",
    "BSD License",
    "BSD 3-Clause",
    "BSD-3-Clause",
    "GNU Library or Lesser General Public License (LGPL)",
    "Microsoft Public License",
    "MIT",
    "MIT License",
    "Python Software Foundation License",
    "ISC License (ISCL)",
    "MIT-0",
]
```

More customization coming soon!