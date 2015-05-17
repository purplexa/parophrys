from parophrys import cli, hostgroup, do
import parophrys


@hostgroup('localhost')
def localhost_group():
    return ['localhost']


@cli.command()
@cli.option('--fqdn', '-f', is_flag=True,
            help='Print the FQDN instead of the short name')
def hostname(fqdn):
    parophrys.config(disable_host_checking=True)
    if fqdn:
        do('hostname -f')
    else:
        do('hostname')
