import click
import paramiko

from contextlib import contextmanager
import json
from multiprocessing.pool import ThreadPool


class Config:
    """This represents the base config object for the current running task."""
    def __init__(self):
        self.hosts = []
        self.hostgroups = {}
        self.ignore_host_keys = False

    def puppetdb(self, connect_string='http://localhost:8080', hostname=None):
        command = ['curl -XGET ',
                   connect_string,
                   '/v3/{} ',]

        if not hostname:
            hostname = 'localhost'

        def query(endpoint, query=None):
            if query:
                try:
                    if json.loads(query):
                        query_string = query
                except:
                    query_string = json.dumps(query)
                else:
                    abort('Received query is poorly formatted')
                command.append("--data-urlencode query='{}'".format(query_string))
                command_string = ''.join(command).format(endpoint)
            else:
                command_string = ''.join(command).format(endpoint)

            return json.loads(do(command=command_string, hosts=hostname)[0])

        self.query = query


config = Config()


@click.group()
@click.option('--host',         '-H',   multiple=True,
              help='Hostnames to run the command against')
@click.option('--hostgroup',    '-G',   multiple=True,
              help='Predefined hostgroups to run the command against')
@click.option('--class', '-C', 'puppet_class', multiple=True,
              help=('Puppet class to query PuppetDB for to determine hosts to '
                    'run the command against'))
@click.option('--query',        '-Q',   multiple=True,
              help=('Raw JSON PuppetDB query to use to determine hosts to run '
                    'the command against'))
@click.option('--puppetdb-connect',     show_default=True,
              default='http://localhost:8080',
              help='Connect string to use with curl to query PuppetDB')
@click.option('--puppetdb-host',        show_default=True,
              default='localhost',
              help='Hostname to use with SSH to access the PuppetDB server')
@click.pass_context
def cli(ctx, host, hostgroup, puppet_class, query, puppetdb_connect, puppetdb_host):
    if not ctx.obj:
        ctx.obj = config
    if not hasattr(config, 'query'):
        if puppetdb_connect:
            if puppetdb_host:
                config.puppetdb(connect_string=puppetdb_connect,
                                hostname=puppetdb_host)
            else:
                config.puppetdb(connect_string=puppetdb_connect)
        else:
            if puppetdb_host:
                config.puppetdb(hostname=puppetdb_host)
    if host:
        config.hosts += host
    if hostgroup:
        for func in hostgroup:
            if func in config.hostgroups.keys():
                config.hosts += ctx.obj.hostgroups[func]()
            else:
                raise click.UsageError(
                    'Hostgroup {} does not exist!'.format(func))
    if puppet_class:
        for role in puppet_class:
            data = config.query(endpoint='resources',
                                query=["and",
                                       ["=", "type", "Class"],
                                       ["~", "title", role]])
            ctx.obj.hosts += [i['certname'] for i in data]

cli.option = click.option


def hostgroup(group_name):
    def hg_decorator(func):
        config.hostgroups[group_name] = func
        return func
    return hg_decorator


def hosts():
    return config.hosts


def ssh_open(host, username=None, password=None):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    if config.ignore_host_keys:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username=username, password=password)
    return ssh


def cmd_exec(command, host, username=None, password=None):
    ssh = ssh_open(host, username=username, password=password)
    stdin, stdout, stderr = ssh.exec_command(command)
    # Need to return ssh so that the object doesn't get garbage collected early.
    return stdin, stdout, stderr, ssh

@contextmanager
def do(command,
       hosts=None,
       username=None,
       password=None):
    """Run an ssh command on a list of hosts."""
    hosts = hosts or config.hosts
    hosts = hosts if isinstance(hosts, list) else [hosts]
    output = dict()
    sshes = list()
    for host in hosts:
        stdin, stdout, stderr, ssh = cmd_exec(command=command,
                                              host=host,
                                              username=username,
                                              password=password)
        output[host] = dict(stdout=stdout, stdin=stdin, stderr=stderr)
        sshes.append(ssh)
    yield output
    for ssh in sshes:
        ssh.close()

def send_file(local, remote, hosts=None, username=None, password=None):
    hosts = hosts or config.hosts
    hosts = hosts if isinstance(hosts, list) else [hosts]
    for host in hosts:
        ssh = ssh_open(host=host, username=username, password=password)
        ftp = ssh.open_sftp()
        ftp.put(local, remote)
        ftp.close()
