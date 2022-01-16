from setuptools import setup, find_packages

with open("README.rst") as fh:
    long_description = fh.read()

setup(
    name="repeated_test",
    packages=find_packages(),
    version="1.0.1",
    description="A quick unittest-compatible framework for repeating a "
                "test function over many fixtures",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license="MIT",
    author="Yann Kaiser",
    author_email="kaiser.yann@gmail.com",
    url="https://github.com/epsy/repeated_test",
    tests_require=['unittest2'],
    python_requires="<3.10",
    install_requires=['six>=1.7'],
    test_suite="repeated_test.tests",
    keywords=['test', 'testing', 'unittest', 'fixtures'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
)
