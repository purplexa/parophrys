import click
import paramiko


class _Environment:
    def __init__(self):
        self.hosts = []
        self.host_groups = []
        self.ignore_host_keys = False


_env = _Environment()


def _process_hosts(ctx, param, value):
    if not ctx.obj:
        ctx.obj = _env
    if param.name == 'host':
        ctx.obj.hosts += value
    if param.name == 'host_group':
        for func in value:
            if func in ctx.obj.host_groups.keys():
                ctx.obj.hosts += func()
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
@click.option('--host-group', '-G', callback=_process_hosts,
              multiple=True, is_eager=True, expose_value=False)
@click.option('--role', '-R', callback=_process_hosts,
              multiple=True, is_eager=True, expose_value=False)
@click.option('--query', '-Q', callback=_process_hosts,
              multiple=True, is_eager=True, expose_value=False)
@click.pass_context
def cli(ctx):
    if not ctx.obj:
        ctx.obj = _env


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
