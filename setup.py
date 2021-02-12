from setuptools import setup, find_packages

setup(
    name='bifrost_ssi_stamper',
    version='v2_2_6',
    description='Datahandling functions for bifrost (later to be API interface)',
    url='https://github.com/ssi-dk/bifrost_ssi_stamper',
    author="Kim Ng, Martin Basterrechea",
    author_email="kimn@ssi.dk",
    packages=find_packages(),
    install_requires=[
        'bifrostlib >= 2.1.7',
    ],
    package_data={"bifrost_ssi_stamper": ['config.yaml']},
    include_package_data=True
)
