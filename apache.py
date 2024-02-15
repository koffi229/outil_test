import yaml
import subprocess
import os

class ApacheConfigGenerator:
    def __init__(self, yaml_file_path):
        with open(yaml_file_path, 'r') as file:
            self.config_data = yaml.safe_load(file)

        # Ajout d'une propriété pour le répertoire de configuration
        self.config_directory = '/chemin/vers/repertoire/config'  # Remplacez par le chemin réel

    def generate_apache_config(self):
        self.generate_general_config()
        self.generate_module_config()
        self.generate_security_config()

    def generate_general_config(self):
        general_config = """
Options: {options}
HostnameLookups: {hostname_lookups}
AllowOverride: {allow_override}
EnableMMAP: {enable_mmap}
EnableSendfile: {enable_sendfile}

<IfModule mod_rewrite.c>
    RewriteEngine On
</IfModule>
        """.format(
            options=" ".join(self.config_data.get('Options', [])),
            hostname_lookups=self.config_data.get('HostnameLookups', 'Off'),
            allow_override=self.config_data.get('AllowOverride', 'None'),
            enable_mmap=self.config_data.get('EnableMMAP', 'Off'),
            enable_sendfile=self.config_data.get('EnableSendfile', 'On')
        )

        with open(os.path.join(self.config_directory, 'general_config.conf'), 'w') as file:
            file.write(general_config)

        print("Generated general_config.conf")

    def generate_module_config(self):
        mpm_module = self.config_data['Modules']['mpm']
        active_mpm_module = self.get_active_mpm_module()

        if active_mpm_module and active_mpm_module != mpm_module:
            print(f"Deactivating current MPM module ({active_mpm_module}) and activating {mpm_module}")
            # Ajoutez ici la logique pour désactiver l'ancien module et activer le nouveau

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
            **self.config_data['MPM_Modules']
        )

        with open(os.path.join(self.config_directory, 'mpm_config.conf'), 'w') as file:
            file.write(mpm_config)

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

        with open(os.path.join(self.config_directory, 'security_config.conf'), 'w') as file:
            file.write(security_config)

        print("Generated security_config.conf")

    def get_active_mpm_module(self):
        try:
            # Exécutez la commande pour obtenir le module MPM actif sur Linux et Apache2
            result = subprocess.run(['apache2ctl', '-t', '-D', 'DUMP_MODULES'], capture_output=True, text=True)

            # Analysez la sortie pour obtenir le module MPM actif
            active_mpm_module = next((line.split()[1] for line in result.stdout.splitlines() if line.startswith('mpm')), None)

            return active_mpm_module
        except Exception as e:
            print(f"Error while determining active MPM module: {e}")
            return None

if __name__ == "__main__":
    path_yaml = input('Veuillez entrer le chemin du fichier yaml svp: ')
    generator = ApacheConfigGenerator(path_yaml)
    generator.generate_apache_config()
