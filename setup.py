from setuptools import setup, find_packages

setup(
    name="stoicquote",
    version="0.1.0",
    url="https://github.com/neelabalan/stoicquote",
    long_description=open("README.md").read(),
    author="neelabalan",
    author_email="neelabalan.n@gmail.com",
    python_requires=">=3.7",
    license="MIT",
    install_requires=[
        "rich",
    ],
    py_modules=["stoicquote"],
    include_package_data=True,
    keywords="quotes",
    packages=find_packages(),
    entry_points={"console_scripts": ["stoicquote = stoicquote:main"]},
    setup_requires=["wheel"],
)
