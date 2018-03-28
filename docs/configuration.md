# HaaS configuration

HaaS reads from an _rc_ file (`~/.haasrc`) at start up.
Any of the keys from the 
[**Defaults**](https://github.com/vin0110/haas/blob/d104b5658699cabf887815aa74f45ed2ab1f0ead/haascli/__init__.py#L15)
dictionary can be set using the format `key=value`.
For example, `identity=~/.haas/osr.pem` sets the location of the AWS identify file.

In addition, it is desirable to configure AWS.
In particular, insert AWS credentials (aws_access_key_id and aws_secret_access_key) into `~/.aws/credentials`.

None of this is needed as all keys can be set (or overridden) in the command line.
