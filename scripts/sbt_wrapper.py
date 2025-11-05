#!/usr/bin/env python3

import subprocess
import sys
import os
import signal
import time

def run_sbt_with_input_handling(sbt_command, java_home):
    """
    Run sbt command with automatic handling of server creation prompts
    """
    env = os.environ.copy()
    env['JAVA_HOME'] = java_home
    env['SBT_OPTS'] = '-Dsbt.server=false -Dsbt.client=false -Dsbt.server.autostart=false'

    # First try to kill any existing sbt servers
    try:
        subprocess.run(['pkill', '-f', 'sbt'], timeout=5, capture_output=True)
    except:
        pass

    # Remove server directories
    try:
        home_dir = os.path.expanduser("~")
        server_dirs = [
            f"{home_dir}/.sbt/1.0/server",
            f"{home_dir}/.sbt/boot",
            "project/.sbtboot",
            "project/.boot"
        ]
        for dir_path in server_dirs:
            if os.path.exists(dir_path):
                subprocess.run(['rm', '-rf', dir_path], capture_output=True)
    except:
        pass

    print(f"Running: {sbt_command}")

    # Try with expect to handle prompts automatically
    try:
        import pexpect
        print(f"Using pexpect to run: {sbt_command}")
        child = pexpect.spawn(sbt_command, env=env, timeout=600)
        child.logfile_read = sys.stdout.buffer  # Show output in real-time

        try:
            while child.isalive():
                index = child.expect([
                    'Create a new server\\? y/n \\(default y\\)',
                    'Create a new server\\? \\[y/n\\]',
                    'sbt thinks that server is already booting',
                    pexpect.EOF,
                    pexpect.TIMEOUT
                ], timeout=30)

                if index in [0, 1, 2]:  # Server creation or booting prompt
                    print("\nDetected server prompt, sending 'n'")
                    child.sendline('n')
                elif index == 3:  # EOF
                    break
                elif index == 4:  # TIMEOUT
                    # Continue if still alive, otherwise break
                    if not child.isalive():
                        break

        except pexpect.EOF:
            pass
        except pexpect.TIMEOUT:
            if child.isalive():
                child.terminate(force=True)

        child.close()
        return child.exitstatus if child.exitstatus is not None else 0

    except ImportError:
        # Fallback: use subprocess with stdin input
        print("pexpect not available, using subprocess with input handling")

        process = subprocess.Popen(
            sbt_command.split(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Send 'n' to stdin immediately to handle any prompts
        try:
            process.stdin.write('n\n')
            process.stdin.flush()
            process.stdin.close()
        except:
            pass

        # Read output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        return process.poll()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: sbt_wrapper.py <java_home> <sbt_command>")
        sys.exit(1)

    java_home = sys.argv[1]
    sbt_command = " ".join(sys.argv[2:])

    exit_code = run_sbt_with_input_handling(sbt_command, java_home)
    sys.exit(exit_code if exit_code is not None else 1)