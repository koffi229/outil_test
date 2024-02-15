import yaml
import subprocess
import os

class ApacheConfigGenerator:
    def __init__(self, yaml_file_path, config_directory='/home/kali/Documents/Mem_test/'):
        self.yaml_file_path = yaml_file_path
        self.config_directory = config_directory
        self.config_data = self.read_config()

    def read_config(self):
        try:
            with open(self.yaml_file_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Fichier YAML introuvable à l'emplacement spécifié: {self.yaml_file_path}")
            return None
        except yaml.YAMLError as e:
            print(f"Erreur de syntaxe YAML dans le fichier: {e}")
            return None

    def generate_apache_config(self):
        if self.config_data:
            self.create_config_directory()
            self.generate_general_config()
            self.generate_module_config()
            self.generate_security_config()

    def create_config_directory(self):
        try:
            os.makedirs(self.config_directory, exist_ok=True)
        except OSError as e:
            print(f"Erreur lors de la création du répertoire de configuration: {e}")

    def generate_general_config(self):
        general_config_template = """
Options {OPTIONS}
HostnameLookups {HOSTNAMELOOKUPS}
AllowOverride {ALLOWOVERRIDE}
EnableMMAP {ENABLEMMAP}
EnableSendfile {ENABLESENDFILE}

<IfModule mod_rewrite.c>
    RewriteEngine On
</IfModule>
"""

        # Convertir les clés en majuscules
        config_values = {key.upper(): self.config_data.get(key, 'DEFAULT_VALUE') for key in ['Options', 'HostnameLookups', 'AllowOverride', 'EnableMMAP', 'EnableSendfile']}
        
        general_config = general_config_template.format(**config_values)

        with open(os.path.join(self.config_directory, 'general_config.conf'), 'w') as file:
            file.write(general_config)

        print("Generated general_config.conf")

    def generate_module_config(self):
        mpm_module = self.config_data['Modules']['mpm']
        active_mpm_module = self.get_active_mpm_module()

        if active_mpm_module and active_mpm_module != mpm_module:
            print(f"Deactivating current MPM module ({active_mpm_module}) and activating {mpm_module}")
            self.deactivate_activate_mpm_module(active_mpm_module, mpm_module)

        self.install_required_modules()

        mpm_config = """
<IfModule {mpm_module}_module>
    StartServers {StartServers}
    MinSpareThreads {MinSpareThreads}
    MaxSpareThreads {MaxSpareThreads}
    ThreadLimit {ThreadLimit}
    ThreadsPerChild {ThreadsPerChild}
    MaxConnectionsPerChild {MaxConnectionsPerChild}
    MaxRequestWorkers {MaxRequestWorkers}
    ServerLimit {ServerLimit}
</IfModule>
""".format(
    mpm_module=mpm_module,
    **self.config_data.get('MPM_Modules', {})  # Ajoutez cette ligne pour vérifier si la clé existe
)


        self.write_config_to_file(mpm_config, 'mpm_config.conf')
        print("Generated mpm_config.conf")

    def generate_security_config(self):
        security_config = """
<IfModule mod_ssl.c>
    SSLProtocol {SSLProtocol}
    SSLCipherSuite {SSLCipherSuite}
    SSLHonorCipherOrder {SSLHonorCipherOrder}
    StrictTransportSecurity {StrictTransportSecurity}
    expose_php {expose_php}
</IfModule>

<IfModule mod_headers.c>
    {XFrameOptions}
    {XContentTypeOptions}
</IfModule>
        """.format(
            **self.config_data['Security'],
            **self.config_data['Rules']
        )

        self.write_config_to_file(security_config, 'security_config.conf')
        print("Generated security_config.conf")

    def write_config_to_file(self, config_content, file_name):
        file_path = os.path.join(self.config_directory, file_name)
        with open(file_path, 'w') as file:
            file.write(config_content)
        self.include_config_in_main(file_path)

    def include_config_in_main(self, file_path):
        apache2_conf_path = '/etc/apache2/apache2.conf'  # Remplacez par le chemin réel
        try:
            with open(apache2_conf_path, 'a') as apache2_conf:
                apache2_conf.write(f"Include {file_path}\n")
            print(f"Included {file_path} in {apache2_conf_path}")
        except Exception as e:
            print(f"Erreur lors de l'inclusion dans {apache2_conf_path}: {e}")

    def get_active_mpm_module(self):
        try:
            result = subprocess.run(['apache2ctl', '-t', '-D', 'DUMP_MODULES'], capture_output=True, text=True)
            active_mpm_module = next((line.split()[1] for line in result.stdout.splitlines() if line.startswith('mpm')), None)
            return active_mpm_module
        except Exception as e:
            print(f"Error while determining active MPM module: {e}")
            return None

    def deactivate_activate_mpm_module(self, active_mpm_module, new_mpm_module):
        try:
            # Ajoutez ici la logique pour désactiver l'ancien module et activer le nouveau
            pass
        except Exception as e:
            print(f"Error while deactivating/activating MPM modules: {e}")

    def install_required_modules(self):
        try:
            for module, value in self.config_data['Modules'].items():
                if value and not self.is_module_installed(module):
                    print(f"Installing module: {module}")
                    self.install_module(module)
        except Exception as e:
            print(f"Error while installing required modules: {e}")

    def is_module_installed(self, module):
        try:
            result = subprocess.run(['apache2ctl', '-t', '-D', 'DUMP_MODULES'], capture_output=True, text=True)
            return module in result.stdout
        except Exception as e:
            print(f"Error while checking if module {module} is installed: {e}")
            return False

    def install_module(self, module):
        try:
            subprocess.run(['a2enmod',module[4:]])
            subprocess.run(['systemctl','restart','apache2'])
            print(f"Module {module} installed successfully.")
        except Exception as e:
            print(f"Error while installing module {module}: {e}")

if __name__ == "__main__":
    #path_yaml = input('Veuillez entrer le chemin du fichier yaml svp: ')
    generator = ApacheConfigGenerator('/home/kali/Documents/Mem_test/template.yaml')
    generator.generate_apache_config()
