# Parophrys - remote task CLI builder

## CLI Usage

```bash
paro --help
```

## Library Usage

```python
from parophrys import cli, do

@cli.command()
@cli.option('--flag', is_flag=True, help='my help text')
@cli.option('--parameter', help='more help text')
def my_command(flag, parameter=None):
    if flag:
        if parameter:
            do('command' + parameter)
        else:
            do('command')
    else:
        print 'did nothing'
```

And to run it:

```bash
paro -R 'Role::Something' my_command --flag --parameter my_file
```
