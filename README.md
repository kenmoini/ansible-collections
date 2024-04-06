# kenmoini Ansible Collections

This is a set of Ansible Collections that I build and distribute.

## Collections

- `kenmoini.kemo` - Just some general collections, mostly helpers
- `kenmoini.phpipam` - Simple modules to use against phpIPAM
- `kenmoini.powerdns_admin` - Some modules to work with the PowerDNS Admin interface

## Development

In order to facilitate quick development, you can simple make a soft link to the Ansible Collections directory.

```bash
# Clone the repo
git clone https://github.com/kenmoini/ansible-collections

# Make a soft link
ln -s $(pwd)/ansible-collections/kenmoini/ ~/.ansible/collections/ansible_collections/
```