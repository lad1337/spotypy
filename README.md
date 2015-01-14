spotypy
=======

##How to install##

# prerequisites
spotypy needs a running mpc server.

```sudo apt-get install mpd

```

Please refer to mpc docs for further instruction for more exotic server OS

todo: add more detailed plugin setup here

Edit /etc/mpd.conf and add this

```
input {
    plugin "curl"
}
input {
    plugin "despotify"
    user "foo"
    password "bar"
}
```


# all
```sh
virtualenv env
. env/bin/activate
pip install -r requirements.txt
```

## start ##
```sh
python server.py
```
