from setuptools import setup, find_packages

setup(
    name="MPRISJukebox",
    version="0.1",
    packages=find_packages(),
    scripts=["say_hello.py"],
    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires=["docutils>=0.3"],
    package_data={
        # If any package contains *.txt or *.rst files, include them:
        "": ["*.mustache", "*.css", "*.js"],
    },
    # metadata to display on PyPI
    author="Jorge Bellon-Castro",
    author_email="jbelloncastro@gmail.com",
    description="Youtube Jukebox",
    long_description="Exposes an HTTP server for requesting songs, searches them in youtube and enqueues the result in a media player using DBus MPRIS interface.",
    keywords="jukebox youtube dbus",
    url="",
    project_urls={"Source Code": "",},
    classifiers=["License :: OSI Approved :: GNU Public License 3"],
    entry_points={
        "console_scripts": [
            "jukebox = jukebox.http:main_func",
            ],
        }
)
