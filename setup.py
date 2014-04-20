from setuptools import setup

setup(
    name = "django-social-graph",
    #url = "http://github.com/suselrd/django-social-graph/",
    author = "Susel Ruiz Duran",
    author_email = "suselrd@gmail.com",
    version = "0.1.1",
    packages = ["social_graph", 'redis_cache'],
    description = "Social Graph for Django + Redis",
    install_requires=['redis>=2.4.5', 'django>=1.6.1', ],
    classifiers = [
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
