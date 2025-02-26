## Docker image downloader

A modified version of Moby's [download-frozen-image-v2.sh](https://github.com/moby/moby/blob/master/contrib/download-frozen-image-v2.sh) script that adds
- Faster and reliable downloads under spotty internet/VPN connection using `aria2c`
- macOS compatibilty (Bash 3.x)
- Better error handling

## Requirements

- `curl`
- `jq`
- `aira2` (`brew install aria2`)

## Usage

`./download-frozen-image-v2.sh pytorch-cuda pytorch/pytorch:2.6.0-cuda11.8-cudnn9-devel`

## Key Modifications

1. **aria2c Integration**: Replaced `curl` with `aria2c` for faster parallel downloads
2. **Bash 3.x Compatibility**: Removed `mapfile` usage for better macOS support
3. **Dependency Checking**: Added upfront checks for required tools
4. **Error Handling**: Improved error messages and handling of empty media types

## Other references

- https://github.com/moby/moby/issues/33700
- https://forums.docker.com/t/docker-pull-cant-resume-when-killed-with-spotty-internet/15822