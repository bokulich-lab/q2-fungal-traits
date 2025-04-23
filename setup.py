# ----------------------------------------------------------------------------
# Copyright (c) 2024, Vinzent Risch.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from setuptools import find_packages, setup

import versioneer

description = (
    "Lifestyle traits annotation of fungal sequences."
)

setup(
    name="q2-fungal-traits",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    license="BSD-3-Clause",
    packages=find_packages(),
    author="Vinzent Risch",
    author_email="risch.vinzent@gmail.com",
    description=description,
    url="https://github.com/bokulich-lab/q2-fugal-traits",
    entry_points={
        "qiime2.plugins": [
            "q2_fungal_traits="
            "q2_fungal_traits"
            ".plugin_setup:plugin"]
    },
    package_data={
        "q2_fungal_traits": ["citations.bib"],
        "q2_fungal_traits.tests": ["data/*"],
    },
    zip_safe=False,
)
