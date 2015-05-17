import click
import paramiko


class _Environment:
    def __init__(self):
        self.hosts = []
        self.hostgroups = {}
        self.ignore_host_keys = False


_env = _Environment()


def _process_hosts(ctx, param, value):
    if not ctx.obj:
        ctx.obj = _env
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
        pass
    if param.name == 'query':
        pass

@click.group()
@click.option('--host', '-H', callback=_process_hosts,
              multiple=True, is_eager=True, expose_value=False)
@click.option('--hostgroup', '-G', callback=_process_hosts,
              multiple=True, is_eager=True, expose_value=False)
@click.option('--role', '-R', callback=_process_hosts,
              multiple=True, is_eager=True, expose_value=False)
@click.option('--query', '-Q', callback=_process_hosts,
              multiple=True, is_eager=True, expose_value=False)
@click.pass_context
def cli(ctx):
    if not ctx.obj:
        ctx.obj = _env


cli.option = click.option


def hostgroup(group_name):
    def hg_decorator(func):
        _env.hostgroups[group_name] = func
        return func
    return hg_decorator


def hosts():
    return _env.hosts


def config(disable_host_checking=None):
    if disable_host_checking != None:
        _env.ignore_host_keys = disable_host_checking


def do(command, hosts=None):
    if not hosts:
        hosts = _env.hosts
    for host in hosts:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        if _env.ignore_host_keys:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host)
        stdin, stdout, stderr = ssh.exec_command(command)
        print stdout.read()
