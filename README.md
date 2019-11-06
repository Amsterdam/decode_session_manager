# Decode Session Manager

This Session Manager is part of the Decode Amsterdam project. For more info check out the [Decode Amsterdam](https://github.com/Amsterdam/decode_passport_scanner) repository.

## Project Setup

When you want to run this server locally first setup a Python Virtual Environment.

First setup up a new virtual environment:
```
$ python3 -m venv venv
```

Then activate it:
```
$ source venv/bin/activate
```

Within this environment you can now setup the needed libraries:
```
$ cd server
$ pip install -r requirements.txt
```

Now the server can be started locally:
```
$ python api.py
```

The location of this API needs to be setup in the Decode Amsterdam PWA. Check out this repository for the details.
