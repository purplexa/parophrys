import click
import paramiko

import json


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


def _process_hosts(ctx, param, value):
    if not ctx.obj:
        ctx.obj = config
    if param.name == 'host':
        ctx.obj.hosts += value
    if param.name == 'hostgroup':
        for func in value:
            if func in ctx.obj.hostgroups.keys():
                ctx.obj.hosts += ctx.obj.hostgroups[func]()
            else:
                raise click.UsageError(
                    'Host group {} does not exist!'.format(func))
    if param.name == 'role':
        if not hasattr(config, 'query'):
            config.puppetdb()
        for role in value:
            data = config.query(endpoint='resources',
                                query=["and",
                                       ["=", "type", "Class"],
                                       ["~", "title", role]])
            ctx.obj.hosts += [i['certname'] for i in data]
    if param.name == 'query':
        pass

@click.group()
@click.option('--host', '-H', callback=_process_hosts,
              multiple=True, expose_value=False)
@click.option('--hostgroup', '-G', callback=_process_hosts,
              multiple=True, expose_value=False)
@click.option('--role', '-R', callback=_process_hosts,
              multiple=True, expose_value=False)
@click.option('--query', '-Q', callback=_process_hosts,
              multiple=True, expose_value=False)
@click.option('--puppetdb-connect', is_eager=True)
@click.option('--puppetdb-host', is_eager=True)
@click.pass_context
def cli(ctx, puppetdb_connect, puppetdb_host):
    if not ctx.obj:
        ctx.obj = config
    if not hasattr(config, 'query'):
        if puppetdb_connect:
            if puppetdb_host:
                config.puppetdb(connect_string=puppetdb_connect,
                                use_ssh=True,
                                hostname=puppetdb_host)
            else:
                config.puppetdb(connect_string=puppetdb_connect)
        else:
            if puppetdb_host:
                config.puppetdb(use_ssh=True,
                                hostname=puppetdb_host)


cli.option = click.option


def hostgroup(group_name):
    def hg_decorator(func):
        config.hostgroups[group_name] = func
        return func
    return hg_decorator


def hosts():
    return config.hosts


def do(command, hosts=None):
    if not hosts:
        hosts = config.hosts
    if not isinstance(hosts, list):
        hosts = [hosts]
    output = []
    for host in hosts:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        if config.ignore_host_keys:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host)
        stdin, stdout, stderr = ssh.exec_command(command)
        output.append(stdout.read())
    return output
