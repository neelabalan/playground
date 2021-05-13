# postinstall

A post linux install script 

## Under development

The config.toml is self explanatory.
I've tried to keep the dependencies and program as simple as possible
and there is no gurantee "SUCCESS" status means the program has installed successfully


```toml
[os-packages]
dependent = 'apt-get'
command = 'sudo apt install -y'
packages = [
	"curl",
	"aria2",
	"software-properties-common",
	"apt-transport-https",
	"feh",
	"python3-pip"
]

[python]
dependent = 'pip3'
command = 'pip3 install'
packages= [
	"pandas",
	"numpy",
	"requests"
]

[cargo]
dependent = 'cargo'
command = 'cargo install'
utilities = ["ripgrep", "exa"]

[npm]
dependent = 'npm'
command = 'npm install'
npm = ["create-react-app", "commander"]


[vscode]
dependent = 'code'
command = 'code --install-extension'
extensions = [
	"bungcip.better-toml",
	"DavidAnson.vscode-markdownlint",
	"msjsdiag.debugger-for-chrome",
	"yzhang.markdown-all-in-one"
]

```

## TODO

- [ ] add more exception handling 
- [x] add logging
- [x] order of execution 
- [ ] need some kind of validation to make sure the program has installed successfully 
