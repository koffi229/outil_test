import yaml
import subprocess
import os

class ApacheConfigGenerator:
    def __init__(self, yaml_file_path, config_directory='/etc/apache2/conf-available/'):
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
            self.generate_php_config()  # Nouvelle méthode pour générer la configuration PHP
            self.generate_security_config()
            self.restart_apache()
            self.include_general_config()  # Nouvelle méthode pour inclure general_config.conf dans apache2.conf

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

        config_values = {key.upper(): self.config_data.get(key, 'DEFAULT_VALUE') for key in ['Options', 'HostnameLookups', 'AllowOverride', 'EnableMMAP', 'EnableSendfile']}
        
        general_config = general_config_template.format(**config_values)

        with open(os.path.join(self.config_directory, 'general_config.conf'), 'w') as file:
            file.write(general_config)

        print("Fichier general_config.conf généré")

    def generate_module_config(self):
        mpm_module = self.config_data['Modules']['mpm']
        active_mpm_module = self.get_active_mpm_module()

        if active_mpm_module and active_mpm_module != mpm_module:
            print(f"Désactivation du module MPM actuel ({active_mpm_module}) et activation de {mpm_module}")
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
    **self.config_data.get('MPM_Modules', {})
)

        self.write_config_to_file(mpm_config, 'mpm_config.conf')
        print("Fichier mpm_config.conf généré")

    def generate_php_config(self):
        php_config_template = """
expose_php {expose_php}
"""

        php_config = php_config_template.format(expose_php=self.config_data.get('PHP', {}).get('expose_php', 'Off'))

        with open(os.path.join(self.config_directory, 'php_config.conf'), 'w') as file:
            file.write(php_config)

        print("Fichier php_config.conf généré")

    def generate_security_config(self):
        security_config = """
<IfModule mod_ssl.c>
    SSLProtocol {SSLProtocol}
    SSLCipherSuite {SSLCipherSuite}
    SSLHonorCipherOrder {SSLHonorCipherOrder}
    StrictTransportSecurity {StrictTransportSecurity}
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
        print("Fichier security_config.conf généré")

    def write_config_to_file(self, config_content, file_name):
        file_path = os.path.join(self.config_directory, file_name)
        with open(file_path, 'w') as file:
            file.write(config_content)
        self.include_config_in_main(file_path)

    def include_config_in_main(self, file_path):
        apache2_conf_path = '/etc/apache2/apache2.conf'
        try:
            with open(apache2_conf_path, 'a') as apache2_conf:
                apache2_conf.write(f"Include {file_path}\n")
            print(f"Inclusion de {file_path} dans {apache2_conf_path}")
        except Exception as e:
            print(f"Erreur lors de l'inclusion dans {apache2_conf_path}: {e}")

    def include_general_config(self):
        self.include_config_in_main(os.path.join(self.config_directory, 'general_config.conf'))

    def get_active_mpm_module(self):
        try:
            result = subprocess.run(['apache2ctl', '-V'], capture_output=True, text=True)
            active_mpm_module = next((line.split()[2] for line in result.stdout.splitlines() if line.startswith('Server MPM')), None)
            return active_mpm_module
        except Exception as e:
            print(f"Erreur lors de la détermination du module MPM actif: {e}")
            return None

    def deactivate_activate_mpm_module(self, active_mpm_module, new_mpm_module):
        try:
            subprocess.run(['sudo', 'a2dismod', 'php8.2', f'mpm_{active_mpm_module}'])
            subprocess.run(['sudo', 'a2enmod', f'mpm_{new_mpm_module}'])
            subprocess.run(['sudo', 'systemctl', 'restart', 'apache2'])
        except Exception as e:
            print(f"Erreur lors de la désactivation/activation des modules MPM : {e}")

    def install_required_modules(self):
        try:
            for module, value in self.config_data['Modules'].items():
                if value and not self.is_module_installed(module):
                    print(f"Installation du module : {module}")
                    getattr(self, f"install_{module}")()
        except Exception as e:
            print(f"Erreur lors de l'installation des modules requis : {e}")

    def is_module_installed(self, module):
        try:
            result = subprocess.run(['apache2ctl', '-t', '-D', 'DUMP_MODULES'], capture_output=True, text=True)
            return module in result.stdout
        except Exception as e:
            print(f"Erreur lors de la vérification de l'ineventstallation du module {module} : {e}")
            return False

    def install_module(self, module):
        try:
            subprocess.run(['sudo', 'a2enmod', module])
            print(f"Module {module} activé avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'activation du module {module} : {e}")

    def restart_apache(self):
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'apache2'])
            print("Apache2 redémarré avec succès.")
        except Exception as e:
            print(f"Erreur lors du redémarrage d'Apache2 : {e}")

    # Ajoutez cette méthode pour installer le module mod_cache
    def install_mod_cache(self):
        try:
            subprocess.run(['sudo', 'a2enmod', 'cache'])
            print("Module mod_cache activé avec succès.")
        except Exception as e:
            print("Erreur lors de l'activation du module mod_cache :", e)

if __name__ == "__main__":
    # Remplacez le chemin avec le chemin absolu de votre fichier YAML
    generator = ApacheConfigGenerator('template.yaml')
    generator.generate_apache_config()
