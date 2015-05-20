from parophrys import cli, config, do


config.ignore_host_keys = True


@cli.command()
@cli.option('--fqdn', '-f', is_flag=True,
            help='Print the FQDN instead of the short name')
def hostname(fqdn):
    if fqdn:
        dashf = ' -f'
    else:
        dashf = ''
    for output in do('hostname' + dashf):
        print output
