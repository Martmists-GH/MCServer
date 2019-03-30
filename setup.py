# External Libraries
from setuptools import setup, find_packages


if __name__ == '__main__':
    setup(
        name="mcserver",
        author="martmists",
        author_email="mail@martmists.com",
        license="All Rights Reserved",
        zip_safe=False,
        version="0.0.1",
        description="A minecraft server written in python",
        long_description="TODO",
        url="https://github.com/martmists/MCServer",
        packages=find_packages(),
        install_requires=["anyio"],
        keywords=["Minecraft", "Python", "Server"],
        classifiers=[
            "Development Status :: 2 - Pre-Alpha",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3.7",
            "Topic :: Software Development :: Libraries :: Python Modules"
        ],
        python_requires=">=3.7")
