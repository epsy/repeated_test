import pathlib
from setuptools import setup, find_packages

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.rst").read_text(encoding='utf-8')

setup(
    name="repeated_test",
    packages=find_packages(),
    version="2.0.0",
    description="A quick unittest-compatible framework for repeating a "
                "test function over many fixtures",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license="MIT",
    author="Yann Kaiser",
    author_email="kaiser.yann@gmail.com",
    url="https://github.com/epsy/repeated_test",
    tests_require=[],
    python_requires=">=3.5",
    install_requires=['six>=1.7'],
    test_suite="repeated_test.tests",
    keywords=['test', 'testing', 'unittest', 'fixtures'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
)
