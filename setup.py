from setuptools import setup, find_packages

setup(
    name="clustertools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "paramiko>=3.5.1",
        "tqdm==4.65.0",
    ],
    entry_points={
        'console_scripts': [
            'cluster2local=clustertools.cluster2local:main',
            'local2cluster=clustertools.local2cluster:main',
        ],
    },
    author="Simone D'Ambrogio",
    description="A Python package for easily transferring files and folders between local machines and remote clusters",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/simonedambrogio/clustertools",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 