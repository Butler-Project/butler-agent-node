from setuptools import find_packages, setup

package_name = 'frontend'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='operador',
    maintainer_email='aricardorodriguez@hotmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
   entry_points={
    'console_scripts': [
         'frontend_server = frontend.frontend.server:main',
         'frontend_cli = frontend.frontend.ollama_client_cli:main',
    ],
    },


)
