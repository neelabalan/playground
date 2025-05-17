#!/usr/bin/env python3

import argparse
import contextlib
import getpass
import logging
import pathlib
import re
import subprocess
import sys
import tempfile
import typing

import paramiko

SSH_HARDENING_POLICY = {
    'PasswordAuthentication': 'no',
    'PermitRootLogin': 'no',
    'ChallengeResponseAuthentication': 'no',
    'PermitEmptyPasswords': 'no',
    'X11Forwarding': 'no',
    'MaxAuthTries': '3',
    'AllowTcpForwarding': 'no',
    'LoginGraceTime': '30',
    'PermitUserEnvironment': 'no',
    'PubkeyAuthentication': 'yes',
}


def setup_logger(debug: bool) -> logging.Logger:
    logger = logging.getLogger('ssh_setup')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

    with tempfile.NamedTemporaryFile(prefix='ssh_setup_', suffix='.log', delete=False) as tmp:
        log_file = tmp.name
        pathlib.Path(log_file).chmod(0o600)

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if debug else logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.debug('Log file created at %s', log_file)
    return logger


logger = setup_logger(debug=True)


def validate_inputs(host: str, user: str, keyfile: str, private_key: typing.Optional[str]):
    if not re.match(r'^[a-zA-Z0-9.-]+$', host):
        raise ValueError('Invalid host format')
    if not re.match(r'^[a-zA-Z0-9_-]+$', user):
        raise ValueError('Invalid username format')
    if not pathlib.Path(keyfile).is_file() or '..' in keyfile:
        raise ValueError('Invalid or insecure keyfile path')
    if private_key and ('..' in private_key or not pathlib.Path(private_key).is_file()):
        raise ValueError('Invalid or insecure private key path')


def read_key(path: str) -> str | typing.NoReturn:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except IOError as e:
        raise ValueError(f'Failed to read key file {path}: {e}')


@contextlib.contextmanager
def ssh_connect(
    host: str, port: int, user: str, password: typing.Optional[str] = None, key_file: typing.Optional[str] = None
) -> typing.Iterator[paramiko.SSHClient]:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if key_file:
            k = paramiko.RSAKey.from_private_key_file(key_file)
            ssh.connect(host, port=port, username=user, pkey=k, timeout=10)
        else:
            ssh.connect(
                host, port=port, username=user, password=password, look_for_keys=False, allow_agent=False, timeout=10
            )
        yield ssh
    except paramiko.AuthenticationException:
        raise ValueError(f'Authentication failed for {user}@{host}')
    except paramiko.SSHException as e:
        raise ValueError(f'SSH connection failed: {e}')
    finally:
        ssh.close()


# TODO: to be integrated later
def use_ssh_copy_id(host: str, port: int, user: str, keyfile: str, password: str) -> bool:
    """Use ssh-copy-id to copy the public key to the remote host."""
    logger.info('Using ssh-copy-id to deploy key...')
    ssh_cmd = ['ssh-copy-id', '-i', keyfile, '-p', str(port), f'{user}@{host}']
    try:
        proc = subprocess.run(ssh_cmd, input=f'{password}\n', text=True, capture_output=True, check=True)
        logger.info('ssh-copy-id output: %s', proc.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error('ssh-copy-id failed: %s', e.stderr)
        return False


def setup_authorized_key(
    sftp: paramiko.SFTPClient, ssh: paramiko.SSHClient, ssh_dir: str, key_data: str, username: str, append: bool
) -> None:
    try:
        if not dir_exists(sftp, ssh_dir):
            sftp.mkdir(ssh_dir, mode=0o700)
            logger.info('Created %s', ssh_dir)
        ak_path = f'{ssh_dir}/authorized_keys'
        # should check if the key already exists before appending?
        with sftp.open(ak_path, 'a' if append else 'w') as f:
            f.write(key_data + '\n')
        sftp.chmod(ak_path, 0o600)
        sftp.chown(ak_path, uid=get_uid(ssh, username), gid=get_gid(ssh, username))
        logger.info('Deployed authorized key to %s', ak_path)
    except IOError as e:
        logger.error('Failed to set up authorized key: %s', e)
        raise


def dir_exists(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp.stat(path)
        return True
    except IOError:
        return False


def get_gid(ssh: paramiko.SSHClient, user: str) -> int | typing.NoReturn:
    try:
        return int(run_remote_cmd(ssh, f'id -g {user}').strip())
    except Exception as e:
        raise ValueError(f'Failed to get GID for {user}: {e}')


def get_uid(ssh: paramiko.SSHClient, user: str) -> int | typing.NoReturn:
    try:
        return int(run_remote_cmd(ssh, f'id -u {user}').strip())
    except Exception as e:
        raise ValueError(f'Failed to get UID for {user}: {e}')


def run_remote_cmd_with_privelge(
    ssh: paramiko.SSHClient, cmd: str, password: str, timeout: float = 30.0
) -> str | typing.NoReturn:
    logger.debug(f'Running command: {cmd}')

    # rough check
    if 'sudo' not in cmd:
        raise ValueError("Use run_remote_cmd for commands not doesn't require user privilege")

    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    stdin.write(password + '\n')
    stdin.flush()

    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    exit_status = stdout.channel.recv_exit_status()

    if exit_status != 0:
        # sudo writes wrong‐password errors to stderr, so capture that
        msg = err.strip() or out.strip()
        if 'incorrect password' in msg.lower():
            raise ValueError('Incorrect sudo password')
        raise RuntimeError(f'Sudo command failed (exit {exit_status}): {msg}')

    return out


def run_remote_cmd(ssh: paramiko.SSHClient, cmd: str) -> str | typing.NoReturn:
    try:
        _, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode('utf-8', errors='replace')
        error = stderr.read().decode('utf-8', errors='replace')
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            raise ValueError(f'Command failed: {cmd}, error: {error}')
        return output
    except Exception as e:
        raise ValueError(f"Failed to run command '{cmd}': {e}")


def apply_hardening(
    ssh: paramiko.SSHClient,
    password: str,
) -> None:
    try:
        filepath = '/etc/ssh/sshd_config'
        backup_cmd = f'sudo cp {filepath} {filepath}.bak'

        # comment then include directives
        comment_include_cmd = "sudo sed -i 's/^Include /#Include /' /etc/ssh/sshd_config"
        run_remote_cmd_with_privelge(ssh, f'sudo -S {comment_include_cmd}', password)
        logger.info('Commented out Include directives in /etc/ssh/sshd_config')

        run_remote_cmd_with_privelge(ssh, f'sudo -S {backup_cmd}', password)
        logger.info(f'Backed up {filepath} to {filepath}.bak')

        for key, value in SSH_HARDENING_POLICY.items():
            # Construct the sed command to replace if found, append if not.
            # This command looks for the key, substitutes the line if found,
            # and appends the line at the end if no substitution occurred.
            sed_cmd = (
                f"grep -q '^#*{key}' {filepath} && "
                f"sudo sed -i 's/^#*{key}.*/{key} {value}/' {filepath} || "
                f"echo '{key} {value}' | sudo tee -a {filepath} > /dev/null"
            )

            run_remote_cmd_with_privelge(ssh, f'sudo -S {sed_cmd}', password)
            logger.info(f'Set or appended "{key} {value}" in {filepath}')

        logger.info('Hardened SSH config written to %s', filepath)
        logger.warning(
            'Remember to restart the SSH service for changes to take effect (e.g., sudo systemctl restart sshd).'
        )

    except Exception as e:
        logger.error('Failed to apply hardening: %s', e)
        raise


def reload_sshd(ssh: paramiko.SSHClient, password: str) -> None:
    try:
        chan = ssh.get_transport().open_session()
        chan.exec_command('sudo -S systemctl reload sshd')
        with chan.makefile('wb') as stdin:
            stdin.write(password + '\n')
            stdin.close()
        exit_status = chan.recv_exit_status()
        if exit_status == 0:
            logger.info('Reloaded sshd with systemctl')
            return
        else:
            logger.warning('systemctl reload failed, exit status: %d', exit_status)
    except Exception as e:
        logger.warning('systemctl reload exception: %s', e)

    # Fallback: kill sshd?
    try:
        pids = run_remote_cmd(ssh, 'pgrep -x sshd').strip().splitlines()
        if not pids:
            logger.error('No sshd process found to kill')
            raise ValueError('No sshd process found')
        for pid in pids:
            run_remote_cmd_with_privelge(ssh, f'sudo -S kill -9 {pid}', password)
        logger.info('Killed sshd process(es): %s', ', '.join(pids))
    except Exception as e:
        logger.error('Failed to reload or restart sshd: %s', e)
        raise


def validate_policy(ssh: paramiko.SSHClient, password: str) -> None:
    try:
        _, stdout, stderr = ssh.exec_command(f'echo "{password}" | sudo -S sshd -T')
        config = stdout.read().decode().lower()
        errors = stderr.read().decode()
        if errors:
            logger.warning(f'Errors from sshd -T: {errors}')
        failed = []
        for key, expected in SSH_HARDENING_POLICY.items():
            key_lower = key.lower()
            for line in config.splitlines():
                if line.startswith(key_lower):
                    actual = line.split()[1]
                    if actual != expected:
                        failed.append(f'{key}={actual} (expected {expected})')
        if failed:
            logger.error('Policy validation failed: %s', ', '.join(failed))
            sys.exit(1)
        logger.info('Policy validated: all hardening settings are correct')
    except paramiko.SSHException as e:
        logger.error('Policy validation failed: %s', e)
        rollback(ssh, password)
        raise


def rollback(ssh: paramiko.SSHClient, password: str, filepath: str = '/etc/ssh/sshd_config') -> None:
    try:
        filepath = '/etc/ssh/sshd_config'
        run_remote_cmd(ssh, f'echo "{password}" | sudo -S cp {filepath}.bak {filepath}')
        logger.info('Rolled back %s from backup', filepath)
        reload_sshd(ssh, password)
    except Exception as e:
        logger.error('Rollback failed: %s', e)


def try_ssh_password(host: str, port: int, user: str, password: str) -> bool:
    try:
        with ssh_connect(host, port, user, password):
            logger.error('Password login still works — expected failure')
            return True
    except ValueError:
        logger.info('Password login correctly disabled')
        return False


def try_ssh_key(host: str, port: int, user: str, key_path: str) -> bool:
    try:
        with ssh_connect(host, port, user, key_file=key_path):
            logger.info('Key-based SSH login successful')
            return True
    except ValueError:
        logger.error('Key-based login failed')
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description='Set up SSH key authentication and harden configuration')
    parser.add_argument('--host', required=True, help='Target host')
    parser.add_argument('--port', type=int, default=22, help='SSH port')
    parser.add_argument('--user', required=True, help='Target username')
    parser.add_argument('--password', required=True, action='store_true', help='Prompt for password')
    parser.add_argument('--keyfile', required=True, help='Public key file path')
    parser.add_argument('--private-key', help='Private key file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument(
        '--append', action='store_true', help='Append the public key to authorized_keys. By default it overrides.'
    )
    args = parser.parse_args()

    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
    logger.info('Starting SSH setup process')

    try:
        validate_inputs(args.host, args.user, args.keyfile, args.private_key)
        password = getpass.getpass('Password: ')
        pubkey = read_key(args.keyfile)

        logger.info('Connecting using password')
        with ssh_connect(args.host, args.port, args.user, password) as ssh:
            with ssh.open_sftp() as sftp:
                setup_authorized_key(sftp, ssh, f'/home/{args.user}/.ssh', pubkey, args.user, args.append)
            apply_hardening(ssh, password)
            validate_policy(ssh, password)
            reload_sshd(ssh, password)

        logger.info('Testing SSH connections...')
        if try_ssh_password(args.host, args.port, args.user, password):
            sys.exit(2)

        private_key_path = args.private_key or str(pathlib.Path.home() / '.ssh' / 'id_rsa')
        if not try_ssh_key(args.host, args.port, args.user, private_key_path):
            sys.exit(3)

        logger.info('SSH setup and hardening completed successfully')
    except Exception as e:
        logger.error('Setup failed: %s', e)
        sys.exit(1)


if __name__ == '__main__':
    main()
