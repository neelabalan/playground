import setuptools

setuptools.setup(
    name="jsondb", 
    version="0.2.0",
    author="neelabalan.n",
    description="jsondb",
    long_description_content_type="text/markdown",
    py_modules=['jsondb'],
    url="https://github.com/neelabalan/jsondb",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
