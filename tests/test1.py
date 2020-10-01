import argparse
if __name__ == "__main__":
    # validate the args.install - using try and except
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i', 
        '--install',
        action  = 'store_true',
        help    = 'installs the packages based on package.toml config in current directory'
    )
    parser.add_argument(
        '-d', 
        '--deploy',   
        action  = 'store_true',
    )
    args = parser.parse_args()
    if args.install:
        print('installation to begin')
