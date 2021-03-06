# mojoName

mojoname plugin to connect Namecoin and register all the .bit domain name.

## Start

You can create your own mojoname.

### Namecoin node

You need to run a namecoin node.

[Namecoin](https://namecoin.org/download/)

You will need to start it as a RPC server.

Example of `~/.namecoin/namecoin.conf` minimal setup:

```
daemon=1
rpcuser=your-name
rpcpassword=your-password
rpcport=8336
server=1
txindex=1
valueencoding=utf8
```

Don't forget to change the `rpcuser` value and `rpcpassword` value!

You can start your node : `./namecoind`

### Create a mojoname site

You will also need to create a site `python MojoNet.py createSite` and regitser the info.

In the site you will need to create a file `./data/<your-site>/data/names.json` with this is it:

```
{}
```

### `mojoname_config.json` file

In `~/.namecoin/mojoname_config.json`

```
{
  "lastprocessed": 223910,
  "MojoNet_path": "/root/MojoNet", # Update with your path
  "privatekey": "", # Update with your private key of your site
  "site": "" # Update with the address of your site
}
```

### Run updater

You can now run the script : `updater/mojoname_updater.py` and wait until it is fully sync (it might take a while).
