from setuptools import setup
import configparser
import os


requirements = []
f = open('requirements.txt', 'r')
while True:
    l = f.readline()
    if l == '':
        break
    requirements.append(l.rstrip())
f.close()

sql_requirements = []
f = open('sql_requirements.txt', 'r')
while True:
    l = f.readline()
    if l == '':
        break
    sql_requirements.append(l.rstrip())
f.close()


setup(
    install_requires=requirements,
    extras_require={
        'sql': sql_requirements,
        'rocksdb': ['shep[rocksdb]~=0.2.2'],
        'redis': ['shep[redis]~=0.2.2'],
    }
    )
