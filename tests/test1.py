# not unit tests 
import argparse
if __name__ == "__main__":
    # validate the args.install - using try and except
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i', 
        '--install',
        action  = 'store_true',
        help    = 'installs the packages based on package.toml config in HOME directory'
    )
    parser.add_argument(
        '-d', 
        '--deploy',   
        action  = 'store_true',
        help    = 'deploys dotfiles from .dotfile in HOME diretory'
    )
    args = parser.parse_args()
    print(args)
    if not args.install and args.deploy:    
        if args.install:
            print('installation to begin')
        if args.deploy:
            print('deploy configs')
    else:
        print('no arguments provided')
