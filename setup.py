from setuptools import setup, find_packages

setup(
    name="django-social-graph",
    url="http://github.com/suselrd/django-social-graph/",
    author="Susel Ruiz Duran",
    author_email="suselrd@gmail.com",
    version="0.3.2",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    description="Social Graph for Django + Redis",
    install_requires=['redis>=2.10.3', 'django>=1.6.1', 'django-redis-cache==1.6.5'],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
        "Environment :: Web Environment",
        "Framework :: Django",
    ],
)
